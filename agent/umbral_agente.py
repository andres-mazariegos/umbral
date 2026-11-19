#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente de Umbral
================
Programa pequeño que corre EN TU COMPUTADORA, te pide permiso, mira qué
puertas (puertos) tienes abiertas y manda esa lista a tu cuenta de Umbral
para que te la explique en lenguaje sencillo.

Funciona en Windows y en Linux. No necesita instalar nada además de Python:
si tienes "psutil" lo aprovecha, y si no, usa las herramientas del sistema
(netstat en Windows, ss en Linux).

Qué SÍ lee:  número de puerto, protocolo, dirección donde escucha, nombre y
             carpeta del programa que lo abrió, sistema operativo y si el
             cortafuegos está encendido.
Qué NO lee:  archivos, contraseñas, historial, fotos, teclas, pantalla ni el
             contenido de lo que viaja por la red. Tampoco cambia nada.

Uso:
    python umbral_agente.py                 primera vez: te pide el código
    python umbral_agente.py --ver           solo muestra lo que enviaría
    python umbral_agente.py --vigilar 30    revisa cada 30 minutos
    python umbral_agente.py --olvidar       desconecta este equipo
"""
import argparse
import csv
import io
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "1.0"
CARPETA = Path.home() / ".umbral"
ARCHIVO = CARPETA / "agente.json"
MAX_PUERTOS = 400


# ----------------------------------------------------------- utilidades

def _ejecutar(comando, segundos=20):
    """Corre un comando del sistema y devuelve su texto (o "" si falla)."""
    try:
        extra = {"creationflags": 0x08000000} if os.name == "nt" else {}   # sin ventana negra en Windows
        r = subprocess.run(comando, capture_output=True, timeout=segundos, **extra)
        return r.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _sistema():
    s = platform.system().lower()
    return {"windows": "windows", "linux": "linux", "darwin": "mac"}.get(s, s[:20])


def _detalle_sistema():
    if _sistema() == "linux":
        try:
            datos = dict(l.strip().split("=", 1) for l in Path("/etc/os-release").read_text().splitlines() if "=" in l)
            return datos.get("PRETTY_NAME", "Linux").strip('"')[:120]
        except Exception:
            pass
    return f"{platform.system()} {platform.release()}".strip()[:120]


def _sin_usuario(ruta):
    """Quita tu nombre de usuario de la ruta: C:\\Users\\ana\\x.exe -> ~\\x.exe"""
    if not ruta:
        return ""
    casa = str(Path.home())
    if ruta.lower().startswith(casa.lower()):
        ruta = "~" + ruta[len(casa):]
    return ruta[:260]


def _partir(direccion):
    """'0.0.0.0:80' / '[::]:22' / '*:68' / '127.0.0.53%lo:53' -> (ip, puerto)"""
    if ":" not in direccion:
        return None
    ip, _, puerto = direccion.rpartition(":")
    ip = ip.strip("[]").split("%")[0]
    if ip in ("*", ""):
        ip = "0.0.0.0"
    try:
        puerto = int(puerto)
    except ValueError:
        return None
    return (ip, puerto) if 0 < puerto < 65536 else None


# ----------------------------------------------------------- recoleccion

def _con_psutil():
    import psutil   # opcional
    encontrados, nombres = [], {}
    for c in psutil.net_connections(kind="inet"):
        es_tcp = c.type == socket.SOCK_STREAM
        if es_tcp and c.status != psutil.CONN_LISTEN:
            continue
        if not c.laddr or not getattr(c.laddr, "port", 0):
            continue
        if not es_tcp and getattr(c, "raddr", None):
            continue
        proceso, ruta = "", ""
        if c.pid:
            if c.pid not in nombres:
                try:
                    p = psutil.Process(c.pid)
                    nombre = p.name()
                    try:
                        exe = p.exe()
                    except Exception:
                        exe = ""
                    nombres[c.pid] = (nombre, exe)
                except Exception:
                    nombres[c.pid] = ("", "")
            proceso, ruta = nombres[c.pid]
        encontrados.append({"puerto": c.laddr.port, "protocolo": "tcp" if es_tcp else "udp",
                            "direccion": c.laddr.ip.split("%")[0], "proceso": proceso, "ruta": ruta})
    return encontrados


def _con_ss():
    """Linux sin psutil: usa `ss -H -tulpn`."""
    encontrados = []
    for linea in _ejecutar(["ss", "-H", "-tulpn"]).splitlines():
        partes = linea.split()
        if len(partes) < 5 or partes[0] not in ("tcp", "udp"):
            continue
        par = _partir(partes[4])
        if not par:
            continue
        m = re.search(r'users:\(\("([^"]+)",pid=(\d+)', linea)
        proceso, ruta = (m.group(1), "") if m else ("", "")
        if m:
            try:
                ruta = os.readlink(f"/proc/{m.group(2)}/exe")
            except Exception:
                ruta = ""
        encontrados.append({"puerto": par[1], "protocolo": partes[0], "direccion": par[0], "proceso": proceso, "ruta": ruta})
    return encontrados


def _con_netstat():
    """Windows sin psutil: usa `netstat -ano` y `tasklist`.
    No depende del idioma de Windows: una conexion TCP esta "escuchando"
    cuando su direccion remota es 0.0.0.0:0 o [::]:0."""
    nombres = {}
    for fila in csv.reader(io.StringIO(_ejecutar(["tasklist", "/FO", "CSV", "/NH"]))):
        if len(fila) >= 2 and fila[1].isdigit():
            nombres[fila[1]] = fila[0]
    encontrados = []
    for linea in _ejecutar(["netstat", "-ano"]).splitlines():
        partes = linea.split()
        if len(partes) < 4 or partes[0] not in ("TCP", "UDP"):
            continue
        if partes[0] == "TCP" and partes[2] not in ("0.0.0.0:0", "[::]:0"):
            continue
        par = _partir(partes[1])
        if not par:
            continue
        encontrados.append({"puerto": par[1], "protocolo": partes[0].lower(), "direccion": par[0],
                            "proceso": nombres.get(partes[-1], ""), "ruta": ""})
    return encontrados


def _cortafuegos():
    """Devuelve 'activo', 'apagado' o 'desconocido'."""
    so = _sistema()
    if so == "windows":
        salida = _ejecutar(["powershell", "-NoProfile", "-Command", "(Get-NetFirewallProfile).Enabled"]).lower().split()
        valores = [v for v in salida if v in ("true", "false", "1", "0")]
        if not valores:
            return "desconocido"
        return "activo" if all(v in ("true", "1") for v in valores) else "apagado"
    if so == "linux":
        try:
            if "enabled=yes" in Path("/etc/ufw/ufw.conf").read_text().lower().replace(" ", ""):
                return "activo"
        except Exception:
            pass
        if _ejecutar(["systemctl", "is-active", "firewalld"]).strip() == "active":
            return "activo"
        reglas = _ejecutar(["nft", "list", "ruleset"])
        if "chain" in reglas and ("drop" in reglas or "reject" in reglas):
            return "activo"
        if Path("/etc/ufw/ufw.conf").exists():
            return "apagado"
    return "desconocido"


def recolectar():
    """Arma el reporte completo. Es exactamente lo que se envia: nada mas."""
    metodo = "psutil"
    try:
        puertos = _con_psutil()
    except Exception:
        puertos = _con_netstat() if _sistema() == "windows" else _con_ss()
        metodo = "sistema"
    vistos, limpios = set(), []
    for p in sorted(puertos, key=lambda x: (x["puerto"], x["protocolo"], x["direccion"])):
        clave = (p["puerto"], p["protocolo"], p["direccion"])
        if clave in vistos:
            continue
        vistos.add(clave)
        p["proceso"] = (p["proceso"] or "")[:80]
        p["ruta"] = _sin_usuario(p["ruta"])
        limpios.append(p)
    return {"version_agente": VERSION, "metodo": metodo, "sistema": _sistema(),
            "detalle_sistema": _detalle_sistema(), "cortafuegos": _cortafuegos(), "puertos": limpios[:MAX_PUERTOS]}


# ----------------------------------------------------------- red

# Abridor propio que solo sabe hablar http y https.
# urllib.request.urlopen tambien abre direcciones file:// (archivos de tu
# computadora). Con este abridor eso ya no es posible, aunque alguien cambie
# la direccion guardada en ~/.umbral/agente.json. (Hallazgo de Semgrep, CWE-939)
_ABRIDOR = urllib.request.OpenerDirector()
for _manejador in (urllib.request.ProxyHandler(), urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(),
                   urllib.request.HTTPDefaultErrorHandler(), urllib.request.HTTPErrorProcessor()):
    _ABRIDOR.add_handler(_manejador)


def _direccion_valida(servidor):
    """Solo acepta direcciones http:// o https:// con un servidor escrito."""
    partes = urllib.parse.urlparse(servidor or "")
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def _pedir(servidor, ruta, datos, llave=None):
    if not _direccion_valida(servidor):
        return 0, {"detail": f"La dirección «{servidor}» no es válida. Debe empezar con http:// o https://"}
    cabeceras = {"Content-Type": "application/json", "User-Agent": f"umbral-agente/{VERSION}"}
    if llave:
        cabeceras["Authorization"] = f"Bearer {llave}"
    peticion = urllib.request.Request(servidor.rstrip("/") + ruta, data=json.dumps(datos).encode("utf-8"),
                                      headers=cabeceras, method="POST")
    try:
        with _ABRIDOR.open(peticion, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            cuerpo = json.loads(e.read().decode("utf-8"))
        except Exception:
            cuerpo = {}
        return e.code, cuerpo
    except (urllib.error.URLError, OSError) as e:
        return 0, {"detail": f"No se pudo llegar a {servidor} ({getattr(e, 'reason', e)}). ¿Está encendido Umbral y escribiste bien la dirección?"}


def _cargar():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _guardar(datos):
    CARPETA.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_text(json.dumps(datos, indent=2), encoding="utf-8")
    try:
        os.chmod(ARCHIVO, 0o600)   # solo tu usuario puede leer la llave
    except Exception:
        pass


# ----------------------------------------------------------- pantalla

def _titulo(texto):
    print("\n" + texto)
    print("-" * len(texto))


def _mostrar(reporte):
    _titulo("Esto es lo que encontró el agente")
    print(f"  Sistema:      {reporte['detalle_sistema']}")
    print(f"  Cortafuegos:  {reporte['cortafuegos']}")
    print(f"  Puertas abiertas: {len(reporte['puertos'])}\n")
    print(f"  {'PUERTO':<8}{'TIPO':<6}{'ESCUCHA EN':<26}PROGRAMA")
    for p in reporte["puertos"]:
        print(f"  {p['puerto']:<8}{p['protocolo']:<6}{p['direccion'][:24]:<26}{p['proceso'] or '(no visible)'}")
    if any(not p["proceso"] for p in reporte["puertos"]):
        aviso = "clic derecho > Ejecutar como administrador" if _sistema() == "windows" else "sudo"
        print(f"\n  Hay programas que no se pudieron ver. Para verlos todos, abre la terminal con: {aviso}")


def _permiso():
    _titulo("Umbral necesita tu permiso")
    print("  Voy a revisar qué puertas (puertos) tiene abiertas esta computadora")
    print("  y a enviar esa lista a tu cuenta de Umbral para explicártela.\n")
    print("  SÍ leo:  número de puerto, programa que lo abrió, sistema y cortafuegos.")
    print("  NO leo:  archivos, contraseñas, historial, fotos ni lo que escribes.")
    print("  NO cambio nada en tu equipo.\n")
    try:
        r = input("  ¿Me das permiso para revisar ahora? (s/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return r in ("s", "si", "sí", "y", "yes")


def _conectar(args, guardado):
    """Primera vez: cambia el codigo de 8 letras por una llave propia de este equipo."""
    _titulo("Conectar este equipo con tu cuenta")
    servidor = args.servidor or guardado.get("servidor") or input("  Dirección de Umbral [http://localhost:8000]: ").strip() or "http://localhost:8000"
    if not re.match(r"^https?://", servidor):
        servidor = "http://" + servidor
    local = re.match(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:|/|$)", servidor)
    if servidor.startswith("http://") and not local:
        print("\n  AVISO: esa dirección no usa https. La lista de puertos viajaría sin cifrar.")
        print("  Está bien para probar en tu red de casa; en internet usa siempre https.")
    codigo = (args.codigo or input("  Código que te muestra Umbral (ej. K7QM-2XRD): ")).strip().upper()
    estado, cuerpo = _pedir(servidor, "/api/agente/enlazar", {
        "codigo": codigo, "sistema": _sistema(), "detalle_sistema": _detalle_sistema()})
    if estado != 200:
        print(f"\n  No se pudo conectar: {cuerpo.get('detail', 'respuesta inesperada del servidor')}")
        return None
    datos = {"servidor": servidor, "llave": cuerpo["llave"], "equipo": cuerpo.get("equipo", "")}
    _guardar(datos)
    print(f"\n  Listo. Este equipo quedó conectado como «{datos['equipo']}».")
    return datos


def _revisar_y_enviar(datos):
    print("\n  Revisando...", flush=True)
    reporte = recolectar()
    _mostrar(reporte)
    estado, cuerpo = _pedir(datos["servidor"], "/api/agente/revisiones", reporte, llave=datos["llave"])
    if estado == 200:
        r = cuerpo.get("resumen", {})
        _titulo("Enviado a Umbral")
        print(f"  Atiéndelo ya: {r.get('urgente', 0)}   Ojo aquí: {r.get('atento', 0)}   Tranquilo: {r.get('tranquilo', 0)}")
        print("  Abre Umbral en tu navegador para leer qué significa cada una.")
        return True
    if estado == 401:
        print("\n  Este equipo fue desconectado desde Umbral. Borra la conexión con --olvidar y vuelve a conectarlo.")
    else:
        print(f"\n  No se pudo enviar: {cuerpo.get('detail', 'error ' + str(estado))}")
    return False


def main():
    ap = argparse.ArgumentParser(description="Agente de Umbral: revisa los puertos abiertos de este equipo con tu permiso.")
    ap.add_argument("--servidor", help="Dirección de Umbral, ej. http://localhost:8000")
    ap.add_argument("--codigo", help="Código de conexión que te muestra Umbral")
    ap.add_argument("--ver", action="store_true", help="Solo muestra lo que se enviaría, sin enviar nada")
    ap.add_argument("--vigilar", type=int, metavar="MIN", help="Repite la revisión cada MIN minutos (mínimo 5)")
    ap.add_argument("--olvidar", action="store_true", help="Borra la conexión guardada en este equipo")
    args = ap.parse_args()

    print("\n  umbral_  agente", VERSION)

    if args.olvidar:
        if ARCHIVO.exists():
            ARCHIVO.unlink()
        print("  Se borró la conexión de este equipo. Para quitarlo de tu cuenta, entra a Umbral > Mis equipos.")
        return 0

    if args.ver:
        reporte = recolectar()
        _mostrar(reporte)
        _titulo("Esto es, tal cual, lo que se enviaría")
        print(json.dumps(reporte, indent=2, ensure_ascii=False))
        return 0

    datos = _cargar()
    if not datos.get("llave") or args.codigo:
        datos = _conectar(args, datos)
        if not datos:
            return 1

    if not _permiso():
        print("\n  Sin permiso no reviso nada. No se envió ningún dato.")
        return 0

    if not args.vigilar:
        return 0 if _revisar_y_enviar(datos) else 1

    minutos = max(5, args.vigilar)
    print(f"\n  Modo vigilancia: revisaré cada {minutos} minutos. Para detenerme pulsa Ctrl + C.")
    try:
        while True:
            _revisar_y_enviar(datos)
            time.sleep(minutos * 60)
    except KeyboardInterrupt:
        print("\n  Vigilancia detenida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
