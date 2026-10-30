# Envio del codigo de verificacion por correo.
# Si configuraste SMTP en el .env, manda el correo de verdad.
# Si no, solo imprime el codigo en la consola del servidor (modo desarrollo).
import smtplib
from email.mime.text import MIMEText

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


def enviar_codigo(destino: str, codigo: str) -> None:
    mensaje = f"Tu codigo de verificacion para Umbral es: {codigo}"

    # Sin SMTP configurado -> modo desarrollo (lo veo en la consola)
    if not SMTP_HOST or not SMTP_USER:
        print(f"[Umbral] Codigo de verificacion para {destino}: {codigo}")
        return

    try:
        correo = MIMEText(mensaje)
        correo["Subject"] = "Tu codigo de Umbral"
        correo["From"] = SMTP_USER
        correo["To"] = destino

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASS)
            servidor.send_message(correo)
    except Exception as e:  # noqa: BLE001
        # Si el correo falla, no quiero tumbar el registro: lo aviso en consola.
        print(f"[Umbral] No se pudo enviar el correo a {destino}: {e}")
        print(f"[Umbral] Codigo de verificacion para {destino}: {codigo}")
