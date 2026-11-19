# Cuenta: registro, confirmacion por correo, entrar, salir y recuperar contraseña.
#
# Reglas que se cumplen aqui:
#  - Las respuestas de registro, reenvio y recuperacion son iguales exista o no
#    el correo: asi nadie puede usar Umbral para averiguar quien tiene cuenta.
#  - Los codigos vencen, se usan una sola vez y se anulan tras varios intentos.
#  - Tras 5 contraseñas malas seguidas la cuenta se bloquea 15 minutos.
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import config, emailer, models, schemas, security
from ..database import get_db
from ..models import ahora

router = APIRouter(prefix="/api/auth", tags=["cuenta"])


def _nuevo_pase(db: Session, usuario: models.Usuario, tipo: str, minutos: int, con_codigo: bool):
    """Anula los pases anteriores del mismo tipo y crea uno nuevo. Devuelve (token, codigo)."""
    db.query(models.Pase).filter(models.Pase.usuario_id == usuario.id, models.Pase.tipo == tipo,
                                 models.Pase.usado.is_(False)).update({"usado": True})
    token, codigo = security.token_largo(), security.codigo_numerico() if con_codigo else None
    db.add(models.Pase(usuario_id=usuario.id, tipo=tipo, hash_token=security.huella(token),
                       hash_codigo=security.huella(f"{usuario.id}:{codigo}") if codigo else None,
                       expira=ahora() + timedelta(minutes=minutos)))
    return token, codigo


def _mandar(tareas: BackgroundTasks, funcion, *args):
    """El correo sale despues de responder: no frena la peticion ni delata nada por el tiempo que tarda."""
    def _seguro():
        try:
            funcion(*args)
        except Exception as e:      # un fallo del correo no debe tumbar la peticion
            print(f"[umbral] No se pudo enviar el correo: {e}", flush=True)
    tareas.add_task(_seguro)


def _extra_dev(codigo=None, token=None):
    """Solo en desarrollo y sin SMTP: devuelve el codigo para poder probar sin correo."""
    if config.MODO_DEV and not emailer.smtp_configurado():
        return {"dev": {"codigo": codigo, "pase": token}}
    return {}


@router.post("/registro", status_code=201)
def registro(datos: schemas.RegistroIn, request: Request, tareas: BackgroundTasks, db: Session = Depends(get_db)):
    security.limitar(request, "registro", maximo=6, segundos=3600)
    respuesta = {"mensaje": "Te enviamos un código de 6 números. Revisa tu correo (y la carpeta de spam).",
                 "correo_real": emailer.smtp_configurado()}
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()

    if usuario and usuario.verificado:
        # Ya existe: no se dice en pantalla. Se le avisa al dueño por correo.
        security.crear_hash(datos.clave)    # mismo trabajo que un registro real, para tardar igual
        _mandar(tareas, emailer.correo_aviso, usuario.email, "Alguien intentó registrar tu correo",
                "Alguien (quizá tú) intentó crear una cuenta con este correo, pero ya tienes una. "
                "Si olvidaste tu contraseña, usa «¿Olvidaste tu contraseña?» en la pantalla de entrada.")
        security.anotar(db, request, "registro_repetido", usuario.id)
        db.commit()
        return respuesta

    if not usuario:
        usuario = models.Usuario(nombre=datos.nombre, email=datos.email, hash_clave=security.crear_hash(datos.clave))
        db.add(usuario)
        db.flush()
    else:   # existia sin confirmar: se queda con los datos nuevos
        usuario.nombre, usuario.hash_clave = datos.nombre, security.crear_hash(datos.clave)

    token, codigo = _nuevo_pase(db, usuario, "confirmar", config.MINUTOS_CODIGO, con_codigo=True)
    security.anotar(db, request, "registro", usuario.id)
    db.commit()
    _mandar(tareas, emailer.correo_confirmacion, usuario.email, usuario.nombre, codigo, token)
    return {**respuesta, **_extra_dev(codigo, token)}


@router.post("/reenviar")
def reenviar(datos: schemas.CorreoIn, request: Request, tareas: BackgroundTasks, db: Session = Depends(get_db)):
    security.limitar(request, "reenviar", maximo=3, segundos=600, extra=datos.email)
    respuesta = {"mensaje": "Si ese correo tiene un registro pendiente, le llegó un código nuevo."}
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if usuario and not usuario.verificado:
        token, codigo = _nuevo_pase(db, usuario, "confirmar", config.MINUTOS_CODIGO, con_codigo=True)
        db.commit()
        _mandar(tareas, emailer.correo_confirmacion, usuario.email, usuario.nombre, codigo, token)
        respuesta.update(_extra_dev(codigo, token))
    return respuesta


@router.post("/confirmar")
def confirmar(datos: schemas.ConfirmarIn, request: Request, response: Response, db: Session = Depends(get_db)):
    security.limitar(request, "confirmar", maximo=15, segundos=600)
    malo = HTTPException(status_code=400, detail="El código no es correcto o ya venció. Pide uno nuevo.")

    if datos.pase:      # llego por el boton del correo
        pase = db.query(models.Pase).filter(models.Pase.hash_token == security.huella(datos.pase),
                                            models.Pase.tipo == "confirmar").first()
    else:               # escribio los 6 numeros
        usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
        if not usuario:
            raise malo
        pase = db.query(models.Pase).filter(models.Pase.usuario_id == usuario.id, models.Pase.tipo == "confirmar",
                                            models.Pase.usado.is_(False)).order_by(models.Pase.id.desc()).first()
        if pase and not security.iguales(pase.hash_codigo or "", security.huella(f"{usuario.id}:{datos.codigo}")):
            pase.intentos += 1
            if pase.intentos >= config.INTENTOS_CODIGO:
                pase.usado = True       # demasiados intentos: ese codigo ya no sirve
            security.anotar(db, request, "codigo_incorrecto", usuario.id)
            db.commit()
            raise malo

    if not pase or pase.usado or pase.expira < ahora():
        raise malo

    usuario = pase.usuario
    pase.usado, usuario.verificado, usuario.ultimo_acceso = True, True, ahora()
    security.anotar(db, request, "correo_confirmado", usuario.id)
    db.commit()
    security.poner_cookie(response, security.crear_sesion(usuario))
    return {"usuario": schemas.UsuarioOut.model_validate(usuario)}


@router.post("/entrar")
def entrar(datos: schemas.EntrarIn, request: Request, response: Response, db: Session = Depends(get_db)):
    security.limitar(request, "entrar", maximo=12, segundos=300)
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()

    if usuario and security.bloqueado(usuario):
        raise HTTPException(status_code=423, detail=f"Por seguridad, esta cuenta está en pausa {config.MINUTOS_BLOQUEO} minutos tras varios intentos fallidos.")

    # Se verifica siempre (aunque el correo no exista) para que tarde lo mismo.
    correcta = security.verificar_clave(datos.clave, usuario.hash_clave if usuario else None)
    if not usuario or not correcta:
        if usuario:
            security.registrar_fallo(usuario)
            security.anotar(db, request, "entrada_fallida", usuario.id)
            db.commit()
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    if not usuario.verificado:
        raise HTTPException(status_code=403, detail="Te falta confirmar tu correo.", headers={"X-Umbral-Motivo": "sin-confirmar"})

    if security.necesita_rehash(usuario.hash_clave):
        usuario.hash_clave = security.crear_hash(datos.clave)
    usuario.intentos_fallidos, usuario.bloqueado_hasta, usuario.ultimo_acceso = 0, None, ahora()
    security.anotar(db, request, "entrada", usuario.id)
    db.commit()
    security.poner_cookie(response, security.crear_sesion(usuario))
    return {"usuario": schemas.UsuarioOut.model_validate(usuario)}


@router.post("/salir")
def salir(response: Response):
    security.quitar_cookie(response)
    return {"mensaje": "Sesión cerrada."}


@router.get("/yo")
def yo(usuario: models.Usuario | None = Depends(security.usuario_opcional)):
    # Sin sesion responde 200 con usuario vacio: preguntar "¿quien soy?" no es un error.
    return {"usuario": schemas.UsuarioOut.model_validate(usuario) if usuario else None}


@router.post("/olvide")
def olvide(datos: schemas.CorreoIn, request: Request, tareas: BackgroundTasks, db: Session = Depends(get_db)):
    security.limitar(request, "olvide", maximo=3, segundos=900, extra=datos.email)
    respuesta = {"mensaje": "Si ese correo tiene cuenta, le llegó un enlace para cambiar la contraseña."}
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if usuario and usuario.verificado:
        token, _ = _nuevo_pase(db, usuario, "restablecer", config.MINUTOS_RESTABLECER, con_codigo=False)
        security.anotar(db, request, "pidio_restablecer", usuario.id)
        db.commit()
        _mandar(tareas, emailer.correo_restablecer, usuario.email, usuario.nombre, token)
        respuesta.update(_extra_dev(token=token))
    return respuesta


@router.post("/restablecer")
def restablecer(datos: schemas.RestablecerIn, request: Request, tareas: BackgroundTasks, db: Session = Depends(get_db)):
    security.limitar(request, "restablecer", maximo=10, segundos=600)
    pase = db.query(models.Pase).filter(models.Pase.hash_token == security.huella(datos.pase),
                                        models.Pase.tipo == "restablecer").first()
    if not pase or pase.usado or pase.expira < ahora():
        raise HTTPException(status_code=400, detail="El enlace ya venció o ya se usó. Pide uno nuevo.")
    usuario = pase.usuario
    try:
        schemas.validar_clave(datos.clave, usuario.email, usuario.nombre)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    pase.usado = True
    usuario.hash_clave = security.crear_hash(datos.clave)
    usuario.version_sesion += 1                 # cierra todas las sesiones abiertas
    usuario.intentos_fallidos, usuario.bloqueado_hasta = 0, None
    security.anotar(db, request, "clave_restablecida", usuario.id)
    db.commit()
    _mandar(tareas, emailer.correo_aviso, usuario.email, "Tu contraseña cambió",
            "La contraseña de tu cuenta de Umbral se acaba de cambiar. Si no fuiste tú, recupérala de inmediato desde la pantalla de entrada.")
    return {"mensaje": "Contraseña actualizada. Ya puedes entrar."}
