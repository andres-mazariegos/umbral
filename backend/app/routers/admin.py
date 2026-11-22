# Seccion de administracion: solo para los correos listados en UMBRAL_ADMINS.
# Muestra cifras generales, las cuentas y la bitacora de seguridad de todo el sitio.
# Los correos salen enmascarados (an***@gmail.com): el administrador cuida el sitio,
# no necesita leer los datos completos de nadie.
from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, security
from ..database import get_db
from ..models import ahora
from .cuenta import NOMBRES_EVENTO

router = APIRouter(prefix="/api/admin", tags=["admin"])

ALERTAS = {"entrada_fallida", "codigo_incorrecto", "registro_repetido", "cuenta_bloqueada"}


def enmascarar(correo: str) -> str:
    usuario, _, dominio = (correo or "").partition("@")
    return f"{usuario[:2]}{'*' * max(3, len(usuario) - 2)}@{dominio}"


def _iso(fecha):
    return fecha.isoformat() + "Z" if fecha else None


@router.get("/resumen")
def resumen(db: Session = Depends(get_db), admin: models.Usuario = Depends(security.usuario_admin)):
    hace_un_dia = ahora() - timedelta(days=1)
    contar = lambda modelo, *filtros: db.query(func.count(modelo.id)).filter(*filtros).scalar() or 0
    niveles = dict(db.query(models.Hallazgo.nivel, func.count(models.Hallazgo.id)).group_by(models.Hallazgo.nivel).all())
    top = db.query(models.Hallazgo.puerto, func.count(models.Hallazgo.id)) \
        .filter(models.Hallazgo.nivel == "urgente").group_by(models.Hallazgo.puerto) \
        .order_by(func.count(models.Hallazgo.id).desc()).limit(6).all()
    sistemas = Counter(s or "otro" for (s,) in db.query(models.Equipo.sistema).filter(models.Equipo.activo.is_(True)).all())
    return {
        "cuentas": contar(models.Usuario),
        "verificadas": contar(models.Usuario, models.Usuario.verificado.is_(True)),
        "bloqueadas": contar(models.Usuario, models.Usuario.bloqueado_hasta > ahora()),
        "equipos": contar(models.Equipo, models.Equipo.activo.is_(True)),
        "revisiones": contar(models.Revision),
        "revisiones_24h": contar(models.Revision, models.Revision.creado >= hace_un_dia),
        "alertas_24h": contar(models.Evento, models.Evento.tipo.in_(ALERTAS), models.Evento.creado >= hace_un_dia),
        "niveles": {n: niveles.get(n, 0) for n in ("urgente", "atento", "tranquilo")},
        "puertos_urgentes": [{"puerto": p, "veces": v} for p, v in top],
        "sistemas": dict(sistemas),
    }


@router.get("/cuentas")
def cuentas(db: Session = Depends(get_db), admin: models.Usuario = Depends(security.usuario_admin)):
    equipos = dict(db.query(models.Equipo.usuario_id, func.count(models.Equipo.id))
                   .filter(models.Equipo.activo.is_(True)).group_by(models.Equipo.usuario_id).all())
    revisiones = dict(db.query(models.Revision.usuario_id, func.count(models.Revision.id))
                      .group_by(models.Revision.usuario_id).all())
    filas = db.query(models.Usuario).order_by(models.Usuario.id.desc()).limit(200).all()
    momento = ahora()
    return {"cuentas": [{
        "id": u.id, "nombre": u.nombre, "correo": enmascarar(u.email), "verificado": u.verificado,
        "bloqueado": bool(u.bloqueado_hasta and u.bloqueado_hasta > momento), "admin": u.es_admin,
        "equipos": equipos.get(u.id, 0), "revisiones": revisiones.get(u.id, 0),
        "creado": _iso(u.creado), "ultimo_acceso": _iso(u.ultimo_acceso),
    } for u in filas]}


@router.get("/bitacora")
def bitacora(solo_alertas: bool = False, db: Session = Depends(get_db),
             admin: models.Usuario = Depends(security.usuario_admin)):
    consulta = db.query(models.Evento, models.Usuario.email) \
        .outerjoin(models.Usuario, models.Usuario.id == models.Evento.usuario_id)
    if solo_alertas:
        consulta = consulta.filter(models.Evento.tipo.in_(ALERTAS))
    filas = consulta.order_by(models.Evento.id.desc()).limit(60).all()
    return {"eventos": [{
        "id": e.id, "tipo": e.tipo, "texto": NOMBRES_EVENTO.get(e.tipo, e.tipo.replace("_", " ")),
        "ip": e.ip, "cuenta": enmascarar(correo) if correo else "(sin cuenta)",
        "alerta": e.tipo in ALERTAS, "fecha": _iso(e.creado),
    } for e, correo in filas]}


@router.post("/cuentas/{usuario_id}/desbloquear")
def desbloquear(usuario_id: int, request: Request, db: Session = Depends(get_db),
                admin: models.Usuario = Depends(security.usuario_admin)):
    usuario = db.get(models.Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Esa cuenta no existe.")
    usuario.bloqueado_hasta = None
    usuario.intentos_fallidos = 0
    security.anotar(db, request, "desbloqueada_por_admin", usuario.id, detalle=f"admin #{admin.id}")
    db.commit()
    return {"mensaje": "La cuenta quedó desbloqueada."}
