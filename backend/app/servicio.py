# Logica compartida de las revisiones: guardar un reporte, resumirlo,
# compararlo con el anterior y armar la respuesta que lee el frontend.
import ipaddress
import json

from sqlalchemy.orm import Session

from . import models
from .interpreter import interpretar, ORDEN_NIVEL


def es_interna(direccion: str) -> bool:
    """True si la puerta solo escucha dentro del propio equipo (127.0.0.1, ::1)."""
    try:
        return ipaddress.ip_address(direccion).is_loopback
    except ValueError:
        return False


def guardar_revision(db: Session, usuario: models.Usuario, equipo: models.Equipo | None,
                     reporte: dict, origen: str, nombre_equipo: str = "") -> models.Revision:
    # 1) Un mismo puerto puede venir varias veces (IPv4, IPv6, varias tarjetas): se junta.
    juntos: dict[tuple, dict] = {}
    for p in reporte["puertos"]:
        clave = (p["puerto"], p["protocolo"])
        item = juntos.setdefault(clave, {**p, "direcciones": [], "alcance": "interno"})
        if p["direccion"] not in item["direcciones"]:
            item["direcciones"].append(p["direccion"])
        if not es_interna(p["direccion"]):
            item["alcance"] = "red"
        item["proceso"] = item["proceso"] or p.get("proceso", "")
        item["ruta"] = item["ruta"] or p.get("ruta", "")

    # 2) Lo que el usuario ya marco como "lo necesito abierto" se respeta en la nueva revision.
    anterior = revision_anterior(db, usuario.id, equipo.id if equipo else None, origen)
    aceptados = {(h.puerto, h.protocolo) for h in anterior.hallazgos if h.estado == "aceptado"} if anterior else set()

    revision = models.Revision(
        usuario_id=usuario.id, equipo_id=equipo.id if equipo else None,
        nombre_equipo=equipo.nombre if equipo else nombre_equipo, origen=origen,
        sistema=reporte.get("sistema", ""), cortafuegos=reporte.get("cortafuegos", "desconocido"),
    )
    db.add(revision)
    db.flush()

    filas = []
    for clave, item in juntos.items():
        info = interpretar(item)
        filas.append(models.Hallazgo(
            revision_id=revision.id, puerto=item["puerto"], protocolo=item["protocolo"],
            direccion=", ".join(item["direcciones"])[:64], alcance=item["alcance"],
            proceso=item["proceso"][:80], ruta=item["ruta"][:260],
            estado="aceptado" if clave in aceptados else "pendiente", **info,
        ))
    filas.sort(key=lambda h: (ORDEN_NIVEL[h.nivel], h.alcance != "red", h.puerto))
    for i, h in enumerate(filas):
        h.orden = i
        db.add(h)
    return revision


def revision_anterior(db: Session, usuario_id: int, equipo_id: int | None, origen: str, antes_de: int | None = None):
    q = db.query(models.Revision).filter(models.Revision.usuario_id == usuario_id)
    q = q.filter(models.Revision.equipo_id == equipo_id) if equipo_id else \
        q.filter(models.Revision.equipo_id.is_(None), models.Revision.origen == origen)
    if antes_de:
        q = q.filter(models.Revision.id < antes_de)
    return q.order_by(models.Revision.id.desc()).first()


def resumen(revision: models.Revision) -> dict:
    r = {"urgente": 0, "atento": 0, "tranquilo": 0, "total": len(revision.hallazgos), "a_la_red": 0, "por_atender": 0}
    for h in revision.hallazgos:
        r[h.nivel] += 1
        r["a_la_red"] += h.alcance == "red"
        r["por_atender"] += h.nivel == "urgente" and h.estado == "pendiente"
    return r


def hallazgo_dict(h: models.Hallazgo) -> dict:
    return {
        "id": h.id, "puerto": h.puerto, "protocolo": h.protocolo, "direccion": h.direccion, "alcance": h.alcance,
        "proceso": h.proceso, "ruta": h.ruta, "servicio": h.servicio, "nivel": h.nivel, "titulo": h.titulo,
        "explicacion": h.explicacion, "riesgo": h.riesgo, "pasos": json.loads(h.pasos or "{}"),
        "senales": json.loads(h.senales or "[]"), "estado": h.estado,
    }


def revision_corta(r: models.Revision) -> dict:
    return {"id": r.id, "equipo_id": r.equipo_id, "nombre_equipo": r.nombre_equipo, "origen": r.origen,
            "sistema": r.sistema, "cortafuegos": r.cortafuegos, "creado": r.creado.isoformat() + "Z", "resumen": resumen(r)}


def revision_completa(db: Session, r: models.Revision) -> dict:
    datos = revision_corta(r)
    datos["hallazgos"] = [hallazgo_dict(h) for h in r.hallazgos]
    previa = revision_anterior(db, r.usuario_id, r.equipo_id, r.origen, antes_de=r.id)
    if previa:
        antes = {(h.puerto, h.protocolo): h for h in previa.hallazgos}
        hoy = {(h.puerto, h.protocolo): h for h in r.hallazgos}
        datos["cambios"] = {
            "contra": previa.id, "fecha": previa.creado.isoformat() + "Z",
            "nuevas": [{"puerto": h.puerto, "protocolo": h.protocolo, "titulo": h.titulo, "nivel": h.nivel}
                       for k, h in hoy.items() if k not in antes],
            "cerradas": [{"puerto": h.puerto, "protocolo": h.protocolo, "titulo": h.titulo, "nivel": h.nivel}
                         for k, h in antes.items() if k not in hoy],
        }
    else:
        datos["cambios"] = None
    return datos


# Reporte de muestra: lo que suele verse en una laptop con Windows descuidada.
# Sirve para conocer Umbral antes de conectar un equipo (o desde el celular).
REPORTE_EJEMPLO = {
    "sistema": "windows", "detalle_sistema": "Windows 11 (ejemplo)", "cortafuegos": "apagado",
    "puertos": [
        {"puerto": 135, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "svchost.exe", "ruta": "C:\\Windows\\System32\\svchost.exe"},
        {"puerto": 139, "protocolo": "tcp", "direccion": "192.168.1.74", "proceso": "System", "ruta": ""},
        {"puerto": 445, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "System", "ruta": ""},
        {"puerto": 3306, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "mysqld.exe", "ruta": "C:\\xampp\\mysql\\bin\\mysqld.exe"},
        {"puerto": 3389, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "svchost.exe", "ruta": "C:\\Windows\\System32\\svchost.exe"},
        {"puerto": 4444, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "actualizador.exe", "ruta": "~\\AppData\\Local\\Temp\\actualizador.exe"},
        {"puerto": 5040, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "svchost.exe", "ruta": "C:\\Windows\\System32\\svchost.exe"},
        {"puerto": 5353, "protocolo": "udp", "direccion": "0.0.0.0", "proceso": "chrome.exe", "ruta": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"},
        {"puerto": 7070, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "AnyDesk.exe", "ruta": "C:\\Program Files (x86)\\AnyDesk\\AnyDesk.exe"},
        {"puerto": 7680, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "svchost.exe", "ruta": "C:\\Windows\\System32\\svchost.exe"},
        {"puerto": 8000, "protocolo": "tcp", "direccion": "127.0.0.1", "proceso": "python.exe", "ruta": "C:\\Python313\\python.exe"},
        {"puerto": 49664, "protocolo": "tcp", "direccion": "0.0.0.0", "proceso": "lsass.exe", "ruta": "C:\\Windows\\System32\\lsass.exe"},
        {"puerto": 57621, "protocolo": "udp", "direccion": "0.0.0.0", "proceso": "Spotify.exe", "ruta": "~\\AppData\\Roaming\\Spotify\\Spotify.exe"},
    ],
}
