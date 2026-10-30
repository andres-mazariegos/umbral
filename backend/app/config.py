# Configuracion del backend de Umbral.
# Casi todo se puede cambiar con variables de entorno (.env), pero traigo
# valores por defecto para que funcione a la primera.
import os

# Clave para firmar los tokens. En produccion se cambia por una secreta.
SECRET_KEY = os.getenv("UMBRAL_SECRET_KEY", "cambia-esta-clave-en-produccion")
ALGORITMO = "HS256"
HORAS_TOKEN = 12  # cuanto dura la sesion

# Base de datos (SQLite en un archivo local)
DATABASE_URL = os.getenv("UMBRAL_DATABASE_URL", "sqlite:///./umbral.db")

# Desde donde puede llamar el frontend
ORIGENES_CORS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Modo desarrollo: si esta activo, al registrarte te devuelvo el codigo de
# verificacion en la respuesta (para probar sin tener correo configurado).
MODO_DEV = os.getenv("UMBRAL_MODO_DEV", "1") == "1"

# Datos para enviar correos de verdad (opcional). Si no los configuras,
# el codigo solo se imprime en la consola del servidor.
SMTP_HOST = os.getenv("UMBRAL_SMTP_HOST", "")
SMTP_PORT = int(os.getenv("UMBRAL_SMTP_PORT", "587"))
SMTP_USER = os.getenv("UMBRAL_SMTP_USER", "")
SMTP_PASS = os.getenv("UMBRAL_SMTP_PASS", "")
