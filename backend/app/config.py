# Configuracion del backend de Umbral.
# Todo se puede cambiar desde el archivo ".env" (copia de .env.example).
# Si no existe, Umbral arranca con valores pensados para probar en tu equipo.
import os
import secrets
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
RAIZ_PROYECTO = RAIZ_BACKEND.parent


def _cargar_env():
    """Lee backend/.env sin depender de librerias externas."""
    archivo = RAIZ_BACKEND / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env()


def _bool(nombre, defecto):
    return os.getenv(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes")


# --- Modo ---
# Desarrollo: el correo se muestra en la consola si no hay SMTP y la cookie
# viaja sin "Secure" porque en tu equipo no hay HTTPS.
MODO_DEV = _bool("UMBRAL_MODO_DEV", "1")

# --- Llave para firmar las sesiones ---
# En desarrollo, si no pusiste una, se genera y se guarda en un archivo local
# para que la sesion no se cierre cada vez que reinicias el servidor.
SECRET_KEY = os.getenv("UMBRAL_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY.startswith("cambia-"):
    if not MODO_DEV:
        raise RuntimeError("Falta UMBRAL_SECRET_KEY en el archivo .env (obligatoria fuera de desarrollo).")
    _archivo_llave = RAIZ_BACKEND / ".llave_dev"
    if not _archivo_llave.exists():
        _archivo_llave.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    SECRET_KEY = _archivo_llave.read_text(encoding="utf-8").strip()

ALGORITMO = "HS256"
HORAS_SESION = 12
NOMBRE_COOKIE = "umbral_sesion"

# --- Base de datos ---
# En tu computadora: un archivo SQLite (backend/umbral.db).
# En Railway: PostgreSQL. Railway entrega la direccion en DATABASE_URL.
DATABASE_URL = (os.getenv("UMBRAL_DATABASE_URL") or os.getenv("DATABASE_URL")
                or f"sqlite:///{(RAIZ_BACKEND / 'umbral.db').as_posix()}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

# --- Direccion publica del sitio (va dentro de los correos) ---
URL_SITIO = os.getenv("UMBRAL_URL_SITIO", "http://localhost:8000").rstrip("/")

ORIGENES_CORS = [o.strip() for o in os.getenv(
    "UMBRAL_ORIGENES", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
).split(",") if o.strip()]

# --- Correo ---
SMTP_HOST = os.getenv("UMBRAL_SMTP_HOST", "")
SMTP_PORT = int(os.getenv("UMBRAL_SMTP_PORT", "587"))
SMTP_USER = os.getenv("UMBRAL_SMTP_USER", "")
SMTP_PASS = os.getenv("UMBRAL_SMTP_PASS", "")
SMTP_TLS = _bool("UMBRAL_SMTP_TLS", "1")
CORREO_REMITENTE = os.getenv("UMBRAL_CORREO_REMITENTE", SMTP_USER or "umbral@localhost")
# Resend: envio por API (HTTPS). Se usa en Railway, donde el puerto SMTP esta cerrado.
RESEND_API_KEY = os.getenv("UMBRAL_RESEND_API_KEY", "")

# --- Administradores ---
# Correos separados por coma. Solo esas cuentas ven la seccion "Administración".
ADMINS = {c.strip().lower() for c in os.getenv("UMBRAL_ADMINS", "").split(",") if c.strip()}

# --- Reglas de seguridad de la cuenta ---
MINUTOS_CODIGO = 15            # vigencia del codigo de confirmacion
MINUTOS_RESTABLECER = 30       # vigencia del enlace para cambiar contraseña
INTENTOS_CODIGO = 5            # intentos antes de invalidar un codigo
INTENTOS_LOGIN = 5             # fallos seguidos antes de bloquear
MINUTOS_BLOQUEO = 15
MINUTOS_ENLACE_EQUIPO = 10     # vigencia del codigo para conectar un equipo

# --- Revision directa ---
# Si la API corre en tu propia computadora puede revisarla sin el agente.
# En un servidor publico se apaga: ahi lo revisado seria el servidor, no tu equipo.
REVISION_LOCAL = _bool("UMBRAL_REVISION_LOCAL", "1" if MODO_DEV else "0")

RUTA_AGENTE = RAIZ_PROYECTO / "agent" / "umbral_agente.py"
RUTA_AGENTE_WINDOWS = RAIZ_PROYECTO / "agent" / "umbral-agente.ps1"
RUTA_WEB = RAIZ_PROYECTO / "frontend" / "dist"
