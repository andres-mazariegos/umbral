# Rutas de revisiones: hacer una revision, listarlas, ver detalle y
# ver solo lo que requiere accion.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..scanner import escanear
from ..interpreter import interpretar
from ..security import get_current_user

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _resumen(hallazgos):
    """Cuenta cuantos hallazgos hay de cada nivel."""
    r = schemas.ResumenNiveles()
    for h in hallazgos:
        if h.nivel == "ok":
            r.ok += 1
        elif h.nivel == "importante":
            r.importante += 1
        else:
            r.revisar += 1
    return r


def _armar_salida(revision):
    hallazgos = revision.hallazgos
    return schemas.RevisionOut(
        id=revision.id,
        objetivo=revision.objetivo,
        origen=revision.origen,
        created_at=revision.created_at,
        resumen=_resumen(hallazgos),
        total=len(hallazgos),
        hallazgos=[schemas.HallazgoOut.model_validate(h) for h in hallazgos],
    )


@router.post("", response_model=schemas.RevisionOut)
def nueva_revision(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    # 1) escaneo los puertos del equipo
    puertos, origen = escanear("127.0.0.1")

    # 2) creo la revision
    revision = models.Revision(usuario_id=usuario.id, objetivo="127.0.0.1", origen=origen)
    db.add(revision)
    db.flush()  # para tener el id de la revision

    # 3) interpreto cada puerto a lenguaje sencillo y lo guardo
    for p in puertos:
        info = interpretar(p["puerto"], p.get("servicio", ""))
        db.add(models.Hallazgo(
            revision_id=revision.id,
            puerto=p["puerto"],
            protocolo=p.get("protocolo", "tcp"),
            servicio=info["servicio"],
            nivel=info["nivel"],
            titulo=info["titulo"],
            explicacion=info["explicacion"],
            riesgo=info["riesgo"],
            recomendacion=info["recomendacion"],
        ))

    db.commit()
    db.refresh(revision)
    return _armar_salida(revision)


@router.get("", response_model=list[schemas.RevisionResumenOut])
def listar_revisiones(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    revisiones = (
        db.query(models.Revision)
        .filter(models.Revision.usuario_id == usuario.id)
        .order_by(models.Revision.created_at.desc())
        .all()
    )
    salida = []
    for r in revisiones:
        salida.append(schemas.RevisionResumenOut(
            id=r.id,
            objetivo=r.objetivo,
            origen=r.origen,
            created_at=r.created_at,
            resumen=_resumen(r.hallazgos),
            total=len(r.hallazgos),
        ))
    return salida


@router.get("/{revision_id}", response_model=schemas.RevisionOut)
def ver_revision(
    revision_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    revision = (
        db.query(models.Revision)
        .filter(models.Revision.id == revision_id, models.Revision.usuario_id == usuario.id)
        .first()
    )
    if not revision:
        raise HTTPException(status_code=404, detail="No encontramos esa revision")
    return _armar_salida(revision)


@router.get("/{revision_id}/recommendations", response_model=list[schemas.HallazgoOut])
def recomendaciones(
    revision_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    revision = (
        db.query(models.Revision)
        .filter(models.Revision.id == revision_id, models.Revision.usuario_id == usuario.id)
        .first()
    )
    if not revision:
        raise HTTPException(status_code=404, detail="No encontramos esa revision")
    # Solo lo que requiere atencion (revisar o importante)
    pendientes = [h for h in revision.hallazgos if h.nivel != "ok"]
    return [schemas.HallazgoOut.model_validate(h) for h in pendientes]
