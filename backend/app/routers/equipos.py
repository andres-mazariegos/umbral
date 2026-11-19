# Equipos conectados y el lado del agente.
#
# Como se conecta un equipo:
#   1. En la web das tu permiso y Umbral te muestra un codigo (vale 10 minutos, un solo uso).
#   2. Corres el agente en tu computadora y escribes el codigo.
#   3. El agente recibe una llave propia. Umbral solo guarda la huella de esa llave.
#   4. Cada revision viaja firmada con la llave. Puedes anularla cuando quieras.
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas, security, servicio
from ..database import get_db
from ..models import ahora

router = APIRouter(prefix="/api", tags=["equipos"])
MAX_EQUIPOS = 10


def _equipo(e: models.Equipo, db: Session) -> dict:
    ultima = db.query(models.Revision).filter(models.Revision.equipo_id == e.id).order_by(models.Revision.id.desc()).first()
    return {"id": e.id, "nombre": e.nombre, "sistema": e.sistema, "detalle_sistema": e.detalle_sistema,
            "creado": e.creado.isoformat() + "Z", "ultima_senal": e.ultima_senal.isoformat() + "Z" if e.ultima_senal else None,
            "ultima_revision": servicio.revision_corta(ultima) if ultima else None}


@router.get("/equipos")
def listar(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    equipos = db.query(models.Equipo).filter(models.Equipo.usuario_id == usuario.id, models.Equipo.activo.is_(True)) \
        .order_by(models.Equipo.id.desc()).all()
    return {"equipos": [_equipo(e, db) for e in equipos]}


@router.post("/equipos/enlace", status_code=201)
def crear_enlace(datos: schemas.EnlaceIn, request: Request, db: Session = Depends(get_db),
                 usuario: models.Usuario = Depends(security.usuario_actual)):
    security.limitar(request, "enlace", maximo=10, segundos=600)
    activos = db.query(models.Equipo).filter(models.Equipo.usuario_id == usuario.id, models.Equipo.activo.is_(True)).count()
    if activos >= MAX_EQUIPOS:
        raise HTTPException(status_code=409, detail=f"Llegaste al máximo de {MAX_EQUIPOS} equipos. Quita uno para conectar otro.")
    codigo = security.codigo_enlace()
    enlace = models.Enlace(usuario_id=usuario.id, hash_codigo=security.huella(codigo), nombre_equipo=datos.nombre,
                           expira=ahora() + timedelta(minutes=config.MINUTOS_ENLACE_EQUIPO))
    db.add(enlace)
    db.commit()
    return {"id": enlace.id, "codigo": codigo, "minutos": config.MINUTOS_ENLACE_EQUIPO}


@router.get("/equipos/enlace/{enlace_id}")
def estado_enlace(enlace_id: int, db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    enlace = db.query(models.Enlace).filter(models.Enlace.id == enlace_id, models.Enlace.usuario_id == usuario.id).first()
    if not enlace:
        raise HTTPException(status_code=404, detail="Ese código ya no existe.")
    revision = None
    if enlace.equipo_id:
        r = db.query(models.Revision).filter(models.Revision.equipo_id == enlace.equipo_id).order_by(models.Revision.id.desc()).first()
        revision = r.id if r else None
    return {"conectado": enlace.usado, "vencido": not enlace.usado and enlace.expira < ahora(),
            "equipo_id": enlace.equipo_id, "revision_id": revision}


@router.patch("/equipos/{equipo_id}")
def renombrar(equipo_id: int, datos: schemas.RenombrarIn, db: Session = Depends(get_db),
              usuario: models.Usuario = Depends(security.usuario_actual)):
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id, models.Equipo.usuario_id == usuario.id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="No encontramos ese equipo.")
    equipo.nombre = datos.nombre
    db.commit()
    return _equipo(equipo, db)


@router.delete("/equipos/{equipo_id}")
def quitar(equipo_id: int, request: Request, db: Session = Depends(get_db),
           usuario: models.Usuario = Depends(security.usuario_actual)):
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id, models.Equipo.usuario_id == usuario.id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="No encontramos ese equipo.")
    security.anotar(db, request, "equipo_quitado", usuario.id, equipo.nombre)
    db.delete(equipo)       # su llave deja de servir al instante; el historial se conserva
    db.commit()
    return {"mensaje": "Equipo desconectado. Su agente ya no puede enviar nada."}


# ------------------------------------------------------------------ agente

@router.get("/agente/descarga")
def descargar_agente():
    if not config.RUTA_AGENTE.exists():
        raise HTTPException(status_code=404, detail="El agente no está disponible en este servidor.")
    return FileResponse(config.RUTA_AGENTE, media_type="text/x-python", filename="umbral_agente.py")


@router.post("/agente/enlazar")
def enlazar(datos: schemas.EnlazarIn, request: Request, db: Session = Depends(get_db)):
    security.limitar(request, "enlazar", maximo=10, segundos=600)     # frena adivinar codigos
    enlace = db.query(models.Enlace).filter(models.Enlace.hash_codigo == security.huella(datos.codigo)).first()
    if not enlace or enlace.usado or enlace.expira < ahora():
        raise HTTPException(status_code=400, detail="El código no existe o ya venció. Genera uno nuevo en Umbral > Mis equipos.")
    llave = security.token_largo()
    equipo = models.Equipo(usuario_id=enlace.usuario_id, nombre=enlace.nombre_equipo, sistema=datos.sistema,
                           detalle_sistema=datos.detalle_sistema, hash_llave=security.huella(llave), ultima_senal=ahora())
    db.add(equipo)
    db.flush()
    enlace.usado, enlace.equipo_id = True, equipo.id
    security.anotar(db, request, "equipo_conectado", enlace.usuario_id, equipo.nombre)
    db.commit()
    return {"llave": llave, "equipo": equipo.nombre}


@router.post("/agente/revisiones")
def recibir_revision(reporte: schemas.ReporteIn, request: Request, db: Session = Depends(get_db),
                     equipo: models.Equipo = Depends(security.equipo_actual)):
    security.limitar(request, "agente", maximo=30, segundos=600, extra=str(equipo.id))
    equipo.ultima_senal = ahora()
    if reporte.sistema:
        equipo.sistema, equipo.detalle_sistema = reporte.sistema, reporte.detalle_sistema
    revision = servicio.guardar_revision(db, equipo.usuario, equipo, reporte.model_dump(), origen="agente")
    db.commit()
    db.refresh(revision)
    return {"revision_id": revision.id, "resumen": servicio.resumen(revision)}
