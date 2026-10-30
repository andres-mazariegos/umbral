# Escaner de puertos de Umbral.
# Uso psutil para leer los puertos que el equipo tiene EN ESCUCHA.
# Lo bueno de psutil es que funciona igual en Windows, Linux (Kali) y Mac,
# sin tener que instalar Nmap. Si algo falla, uso un modo simulado de respaldo.
import socket

import psutil


def _nombre_servicio(puerto: int, protocolo: str = "tcp") -> str:
    """Intenta ponerle nombre al puerto (ssh, http, etc.)."""
    try:
        return socket.getservbyport(puerto, protocolo)
    except OSError:
        return ""


def _escaneo_simulado():
    """Respaldo por si psutil no puede leer nada (algunos permisos)."""
    puertos = [22, 80, 139, 445, 3306, 443]
    lista = [{"puerto": p, "protocolo": "tcp", "servicio": _nombre_servicio(p)} for p in puertos]
    return lista, "simulado"


def escanear(objetivo: str = "127.0.0.1"):
    """
    Devuelve (lista_de_puertos, origen).
    Cada puerto es un dict: {puerto, protocolo, servicio}.
    """
    try:
        encontrados = {}
        for conexion in psutil.net_connections(kind="inet"):
            # Solo me interesan los que estan esperando conexiones (LISTEN)
            if conexion.status == psutil.CONN_LISTEN and conexion.laddr:
                puerto = conexion.laddr.port
                protocolo = "tcp" if conexion.type == socket.SOCK_STREAM else "udp"
                # Evito repetir el mismo puerto
                if puerto not in encontrados:
                    encontrados[puerto] = {
                        "puerto": puerto,
                        "protocolo": protocolo,
                        "servicio": _nombre_servicio(puerto, protocolo),
                    }

        if not encontrados:
            return _escaneo_simulado()

        lista = sorted(encontrados.values(), key=lambda x: x["puerto"])
        return lista, "psutil"

    except (psutil.AccessDenied, PermissionError, OSError):
        # En algunos sistemas leer todas las conexiones pide permisos de admin.
        return _escaneo_simulado()
