# Revisiones: verlas, compararlas, marcar lo que ya atendiste y el resumen del panel.
import importlib.util

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config, emailer, interpreter, models, schemas, security, servicio
from ..database import get_db

router = APIRouter(prefix="/api", tags=["revisiones"])


def _mia(db: Session, usuario: models.Usuario, revision_id: int) -> models.Revision:
    # Siempre se filtra por dueño: nadie puede leer la revision de otra persona cambiando el numero.
    r = db.query(models.Revision).filter(models.Revision.id == revision_id, models.Revision.usuario_id == usuario.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="No encontramos esa revisión.")
    return r


@router.get("/estado")
def estado():
    """Lo que el frontend necesita saber del servidor antes de iniciar sesion."""
    return {"revision_directa": config.REVISION_LOCAL, "correo_real": emailer.correo_configurado(), "modo_dev": config.MODO_DEV}


@router.get("/puertos/{puerto}")
def ficha(puerto: int, request: Request):
    security.limitar(request, "ficha", maximo=60, segundos=60)
    if not 1 <= puerto <= 65535:
        raise HTTPException(status_code=422, detail="Los puertos van del 1 al 65535.")
    return interpreter.ficha_publica(puerto)


@router.get("/panel")
def panel(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    ultimas = db.query(models.Revision).filter(models.Revision.usuario_id == usuario.id) \
        .order_by(models.Revision.id.desc()).limit(40).all()
    vistos, por_equipo = set(), []
    for r in ultimas:                       # la mas reciente de cada equipo
        clave = r.equipo_id or f"{r.origen}"
        if clave not in vistos:
            vistos.add(clave)
            por_equipo.append(r)
    pendientes = []
    for r in por_equipo:
        for h in r.hallazgos:
            if h.nivel == "urgente" and h.estado == "pendiente":
                pendientes.append({**servicio.hallazgo_dict(h), "revision_id": r.id, "nombre_equipo": r.nombre_equipo})
    equipos = db.query(models.Equipo).filter(models.Equipo.usuario_id == usuario.id, models.Equipo.activo.is_(True)).count()
    return {"equipos": equipos, "revisiones": len(ultimas), "recientes": [servicio.revision_corta(r) for r in por_equipo[:6]],
            "pendientes": pendientes[:8], "revision_directa": config.REVISION_LOCAL}


@router.get("/revisiones")
def listar(equipo_id: int | None = None, db: Session = Depends(get_db),
           usuario: models.Usuario = Depends(security.usuario_actual)):
    q = db.query(models.Revision).filter(models.Revision.usuario_id == usuario.id)
    if equipo_id:
        q = q.filter(models.Revision.equipo_id == equipo_id)
    return {"revisiones": [servicio.revision_corta(r) for r in q.order_by(models.Revision.id.desc()).limit(100).all()]}


@router.get("/revisiones/{revision_id}")
def ver(revision_id: int, db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    return servicio.revision_completa(db, _mia(db, usuario, revision_id))


@router.delete("/revisiones/{revision_id}")
def borrar(revision_id: int, db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    db.delete(_mia(db, usuario, revision_id))
    db.commit()
    return {"mensaje": "Revisión borrada."}


@router.patch("/hallazgos/{hallazgo_id}")
def marcar(hallazgo_id: int, datos: schemas.EstadoIn, db: Session = Depends(get_db),
           usuario: models.Usuario = Depends(security.usuario_actual)):
    h = db.query(models.Hallazgo).join(models.Revision).filter(
        models.Hallazgo.id == hallazgo_id, models.Revision.usuario_id == usuario.id).first()
    if not h:
        raise HTTPException(status_code=404, detail="No encontramos ese hallazgo.")
    h.estado = datos.estado
    db.commit()
    return servicio.hallazgo_dict(h)


@router.post("/revisiones/directa", status_code=201)
def directa(request: Request, db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    """Revisa la computadora donde corre la API. Solo existe cuando Umbral corre en tu propio equipo."""
    if not config.REVISION_LOCAL:
        raise HTTPException(status_code=403, detail="En este servidor las revisiones se hacen con el agente, desde tu equipo.")
    security.limitar(request, "directa", maximo=20, segundos=600)
    if not config.RUTA_AGENTE.exists():
        raise HTTPException(status_code=500, detail="Falta el archivo del agente en el servidor.")
    # Se reutiliza el mismo codigo del agente: una sola forma de leer puertos.
    spec = importlib.util.spec_from_file_location("umbral_agente", config.RUTA_AGENTE)
    agente = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agente)
    reporte = schemas.ReporteIn.model_validate(agente.recolectar()).model_dump()
    revision = servicio.guardar_revision(db, usuario, None, reporte, origen="directa", nombre_equipo="Este equipo")
    db.commit()
    db.refresh(revision)
    return {"revision_id": revision.id, "resumen": servicio.resumen(revision)}


@router.post("/revisiones/ejemplo", status_code=201)
def ejemplo(request: Request, db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    """Crea una revision de muestra para conocer Umbral sin conectar nada (util desde el celular)."""
    security.limitar(request, "ejemplo", maximo=10, segundos=600)
    reporte = schemas.ReporteIn.model_validate(servicio.REPORTE_EJEMPLO).model_dump()
    revision = servicio.guardar_revision(db, usuario, None, reporte, origen="ejemplo", nombre_equipo="Laptop de ejemplo")
    db.commit()
    db.refresh(revision)
    return {"revision_id": revision.id, "resumen": servicio.resumen(revision)}
