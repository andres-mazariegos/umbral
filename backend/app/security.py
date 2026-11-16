# Seguridad de la cuenta: contraseñas, sesiones, codigos de un solo uso,
# limite de intentos y bitacora.
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import config, models
from .database import get_db
from .models import ahora

# Argon2id: el algoritmo recomendado hoy para guardar contraseñas.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=2)
# Hash de relleno para tardar lo mismo cuando el correo no existe
# (asi no se puede adivinar que correos estan registrados midiendo el tiempo).
_HASH_RELLENO = _hasher.hash("umbral-relleno-" + secrets.token_hex(8))


def crear_hash(clave: str) -> str:
    return _hasher.hash(clave)


def verificar_clave(clave: str, hash_guardado: str | None) -> bool:
    try:
        return _hasher.verify(hash_guardado or _HASH_RELLENO, clave) and hash_guardado is not None
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False


def necesita_rehash(hash_guardado: str) -> bool:
    return _hasher.check_needs_rehash(hash_guardado)


# ---------- codigos y enlaces de un solo uso ----------
# En la base solo se guarda la huella (SHA-256 con la llave del servidor).
# Si alguien robara la base, no podria usar los codigos ni las llaves.

def huella(texto: str) -> str:
    return hmac.new(config.SECRET_KEY.encode(), texto.encode(), hashlib.sha256).hexdigest()


def token_largo() -> str:
    return secrets.token_urlsafe(32)


def codigo_numerico() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


_ALFABETO_ENLACE = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin O/0, I/1, L para dictarlo sin errores


def codigo_enlace() -> str:
    crudo = "".join(secrets.choice(_ALFABETO_ENLACE) for _ in range(8))
    return f"{crudo[:4]}-{crudo[4:]}"


def iguales(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


# ---------- sesiones (JWT dentro de una cookie HttpOnly) ----------

def crear_sesion(usuario: models.Usuario) -> str:
    datos = {
        "sub": str(usuario.id),
        "ver": usuario.version_sesion,
        "iat": int(time.time()),
        "exp": int(time.time()) + config.HORAS_SESION * 3600,
    }
    return jwt.encode(datos, config.SECRET_KEY, algorithm=config.ALGORITMO)


def poner_cookie(respuesta, token: str):
    respuesta.set_cookie(
        config.NOMBRE_COOKIE, token,
        max_age=config.HORAS_SESION * 3600,
        httponly=True,                      # JavaScript no puede leerla (frena robo por XSS)
        samesite="strict",                  # no viaja en peticiones de otros sitios (frena CSRF)
        secure=not config.MODO_DEV,         # solo por HTTPS fuera de desarrollo
        path="/",
    )


def quitar_cookie(respuesta):
    respuesta.delete_cookie(config.NOMBRE_COOKIE, path="/")


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> models.Usuario:
    error = HTTPException(status_code=401, detail="Tu sesión terminó. Vuelve a entrar.")
    token = request.cookies.get(config.NOMBRE_COOKIE)
    if not token:
        raise error
    try:
        datos = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITMO])
        usuario = db.get(models.Usuario, int(datos["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise error
    if not usuario or not usuario.verificado or datos.get("ver") != usuario.version_sesion:
        raise error
    return usuario


def usuario_opcional(request: Request, db: Session = Depends(get_db)) -> models.Usuario | None:
    try:
        return usuario_actual(request, db)
    except HTTPException:
        return None


def equipo_actual(request: Request, db: Session = Depends(get_db)) -> models.Equipo:
    """Identifica al agente por su llave (cabecera Authorization: Bearer ...)."""
    cabecera = request.headers.get("authorization", "")
    if not cabecera.lower().startswith("bearer ") or len(cabecera) > 200:
        raise HTTPException(status_code=401, detail="Falta la llave del equipo.")
    equipo = db.query(models.Equipo).filter(
        models.Equipo.hash_llave == huella(cabecera[7:].strip()), models.Equipo.activo.is_(True)
    ).first()
    if not equipo:
        raise HTTPException(status_code=401, detail="Este equipo ya no está conectado a Umbral.")
    return equipo


# ---------- limite de intentos ----------

_ventanas: dict[str, deque] = defaultdict(deque)


def ip_de(request: Request) -> str:
    return (request.client.host if request.client else "") or "desconocida"


def limitar(request: Request, nombre: str, maximo: int, segundos: int, extra: str = ""):
    """Corta con 429 si esta IP (o IP + dato extra) rebasa `maximo` en `segundos`."""
    clave = f"{nombre}|{ip_de(request)}|{extra}"
    cola = _ventanas[clave]
    limite = time.monotonic() - segundos
    while cola and cola[0] < limite:
        cola.popleft()
    if len(cola) >= maximo:
        espera = max(1, int(cola[0] - limite))
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos seguidos. Espera un momento y vuelve a intentar.",
            headers={"Retry-After": str(espera)},
        )
    cola.append(time.monotonic())
    if len(_ventanas) > 20000:      # no dejar crecer la memoria sin control
        for k in [k for k, v in _ventanas.items() if not v][:5000]:
            _ventanas.pop(k, None)


def reiniciar_limites():
    _ventanas.clear()


# ---------- bitacora ----------

def anotar(db: Session, request: Request | None, tipo: str, usuario_id: int | None = None, detalle: str = ""):
    db.add(models.Evento(
        usuario_id=usuario_id, tipo=tipo,
        ip=ip_de(request) if request else "", detalle=detalle[:200],
    ))


def bloqueado(usuario: models.Usuario) -> bool:
    return bool(usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora())


def registrar_fallo(usuario: models.Usuario):
    usuario.intentos_fallidos += 1
    if usuario.intentos_fallidos >= config.INTENTOS_LOGIN:
        usuario.bloqueado_hasta = ahora() + timedelta(minutes=config.MINUTOS_BLOQUEO)
        usuario.intentos_fallidos = 0
