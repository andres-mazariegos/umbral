# Ajustes de la cuenta: nombre, contraseña, actividad reciente y borrado.
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import emailer, models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/cuenta", tags=["cuenta"])

NOMBRES_EVENTO = {
    "registro": "Creaste la cuenta", "correo_confirmado": "Confirmaste tu correo", "entrada": "Entraste a tu cuenta",
    "entrada_fallida": "Contraseña incorrecta", "codigo_incorrecto": "Código de confirmación incorrecto",
    "pidio_restablecer": "Pediste cambiar la contraseña", "clave_restablecida": "Contraseña restablecida por correo",
    "clave_cambiada": "Cambiaste la contraseña", "sesiones_cerradas": "Cerraste todas las sesiones",
    "equipo_conectado": "Conectaste un equipo", "equipo_quitado": "Quitaste un equipo",
    "registro_repetido": "Intentaron registrar tu correo otra vez", "nombre_cambiado": "Cambiaste tu nombre",
    "cuenta_bloqueada": "Cuenta bloqueada por intentos fallidos", "desbloqueada_por_admin": "Un administrador desbloqueó la cuenta",
}


@router.patch("/nombre")
def cambiar_nombre(datos: schemas.NombreIn, request: Request, db: Session = Depends(get_db),
                   usuario: models.Usuario = Depends(security.usuario_actual)):
    usuario.nombre = datos.nombre
    security.anotar(db, request, "nombre_cambiado", usuario.id)
    db.commit()
    return {"usuario": schemas.UsuarioOut.model_validate(usuario)}


@router.post("/clave")
def cambiar_clave(datos: schemas.CambiarClaveIn, request: Request, response: Response, tareas: BackgroundTasks,
                  db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    security.limitar(request, "cambiar_clave", maximo=8, segundos=600)
    if not security.verificar_clave(datos.actual, usuario.hash_clave):
        security.anotar(db, request, "entrada_fallida", usuario.id, "al cambiar la contraseña")
        db.commit()
        raise HTTPException(status_code=400, detail="Tu contraseña actual no coincide.")
    if datos.actual == datos.nueva:
        raise HTTPException(status_code=422, detail="La contraseña nueva debe ser distinta a la actual.")
    try:
        schemas.validar_clave(datos.nueva, usuario.email, usuario.nombre)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    usuario.hash_clave = security.crear_hash(datos.nueva)
    usuario.version_sesion += 1
    security.anotar(db, request, "clave_cambiada", usuario.id)
    db.commit()
    security.poner_cookie(response, security.crear_sesion(usuario))   # esta sesion sigue; las demas se cierran
    tareas.add_task(_aviso, usuario.email)
    return {"mensaje": "Contraseña actualizada. Las demás sesiones se cerraron."}


def _aviso(correo):
    try:
        emailer.correo_aviso(correo, "Tu contraseña cambió",
                             "La contraseña de tu cuenta de Umbral se acaba de cambiar. Si no fuiste tú, recupérala desde la pantalla de entrada.")
    except Exception as e:
        print(f"[umbral] No se pudo enviar el aviso: {e}", flush=True)


@router.post("/cerrar-sesiones")
def cerrar_sesiones(request: Request, response: Response, db: Session = Depends(get_db),
                    usuario: models.Usuario = Depends(security.usuario_actual)):
    usuario.version_sesion += 1
    security.anotar(db, request, "sesiones_cerradas", usuario.id)
    db.commit()
    security.poner_cookie(response, security.crear_sesion(usuario))
    return {"mensaje": "Se cerraron las sesiones en los demás dispositivos."}


@router.get("/actividad")
def actividad(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.usuario_actual)):
    eventos = db.query(models.Evento).filter(models.Evento.usuario_id == usuario.id) \
        .order_by(models.Evento.id.desc()).limit(25).all()
    return {"eventos": [{"tipo": e.tipo, "texto": NOMBRES_EVENTO.get(e.tipo, e.tipo), "ip": e.ip, "detalle": e.detalle,
                         "alerta": e.tipo in ("entrada_fallida", "codigo_incorrecto", "registro_repetido"),
                         "fecha": e.creado.isoformat() + "Z"} for e in eventos]}


@router.post("/eliminar")
def eliminar(datos: schemas.ClaveIn, request: Request, response: Response, db: Session = Depends(get_db),
             usuario: models.Usuario = Depends(security.usuario_actual)):
    security.limitar(request, "eliminar", maximo=5, segundos=600)
    if not security.verificar_clave(datos.clave, usuario.hash_clave):
        raise HTTPException(status_code=400, detail="La contraseña no coincide.")
    db.delete(usuario)      # se llevan en cascada equipos, revisiones, hallazgos y bitacora
    db.commit()
    security.quitar_cookie(response)
    return {"mensaje": "Tu cuenta y todos sus datos se borraron."}
