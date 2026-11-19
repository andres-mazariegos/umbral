# Envio de correos de Umbral.
# Con SMTP configurado en .env el correo sale de verdad. Sin SMTP (modo
# desarrollo) se imprime en la consola del servidor para poder probar.
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from . import config


def smtp_configurado() -> bool:
    return bool(config.SMTP_HOST)


def _plantilla(titulo: str, parrafos: list[str], boton: tuple[str, str] | None, codigo: str | None) -> str:
    cuerpo = "".join(f'<p style="margin:0 0 14px;font-size:16px;line-height:1.55;color:#2a2722">{escape(p)}</p>' for p in parrafos)
    if codigo:
        cuerpo += (f'<p style="margin:22px 0;font-family:Consolas,Menlo,monospace;font-size:34px;letter-spacing:10px;'
                   f'color:#0d0c0a;background:#c8f03c;padding:16px 22px;display:inline-block">{escape(codigo)}</p>')
    if boton:
        cuerpo += (f'<p style="margin:8px 0 22px"><a href="{escape(boton[1], quote=True)}" style="background:#0d0c0a;color:#f1eadb;'
                   f'text-decoration:none;padding:14px 22px;font-size:16px;display:inline-block">{escape(boton[0])}</a></p>'
                   f'<p style="margin:0 0 14px;font-size:13px;color:#6b665c;word-break:break-all">Si el botón no abre, copia este enlace: {escape(boton[1])}</p>')
    return (f'<div style="background:#f1eadb;padding:32px 16px;font-family:Arial,Helvetica,sans-serif">'
            f'<div style="max-width:520px;margin:0 auto;background:#fffdf7;padding:34px 30px;border-top:6px solid #c8f03c">'
            f'<p style="margin:0 0 22px;font-family:Consolas,Menlo,monospace;font-size:15px;color:#0d0c0a">umbral_</p>'
            f'<h1 style="margin:0 0 18px;font-size:24px;line-height:1.2;color:#0d0c0a">{escape(titulo)}</h1>{cuerpo}'
            f'<p style="margin:26px 0 0;font-size:13px;color:#6b665c">Si tú no pediste esto, ignora el correo: nadie puede entrar a tu cuenta sin el código.</p>'
            f'</div></div>')


def enviar(destino: str, asunto: str, titulo: str, parrafos: list[str],
           boton: tuple[str, str] | None = None, codigo: str | None = None) -> bool:
    """Devuelve True si el correo salio por SMTP, False si solo se mostro en consola."""
    texto = "\n\n".join(parrafos)
    if codigo:
        texto += f"\n\nCódigo: {codigo}"
    if boton:
        texto += f"\n\n{boton[0]}: {boton[1]}"

    if not smtp_configurado():
        print("\n" + "=" * 64)
        print(f"  CORREO (modo desarrollo, no se envió) -> {destino}")
        print(f"  Asunto: {asunto}")
        print("-" * 64)
        print(texto)
        print("=" * 64 + "\n", flush=True)
        return False

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = f"Umbral <{config.CORREO_REMITENTE}>"
    mensaje["To"] = destino
    mensaje.set_content(texto)
    mensaje.add_alternative(_plantilla(titulo, parrafos, boton, codigo), subtype="html")

    if config.SMTP_PORT == 465:
        servidor = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15, context=ssl.create_default_context())
    else:
        servidor = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
    with servidor:
        if config.SMTP_PORT != 465 and config.SMTP_TLS:
            servidor.starttls(context=ssl.create_default_context())
        if config.SMTP_USER:
            servidor.login(config.SMTP_USER, config.SMTP_PASS)
        servidor.send_message(mensaje)
    return True


def correo_confirmacion(destino: str, nombre: str, codigo: str, token: str) -> bool:
    return enviar(
        destino, f"{codigo} es tu código de Umbral", f"{nombre.split()[0]}, confirma tu correo",
        ["Falta un paso para abrir tu cuenta. Escribe este código en la pantalla de confirmación "
         f"o toca el botón. Vence en {config.MINUTOS_CODIGO} minutos."],
        boton=("Confirmar mi correo", f"{config.URL_SITIO}/confirmar?pase={token}"), codigo=codigo,
    )


def correo_restablecer(destino: str, nombre: str, token: str) -> bool:
    return enviar(
        destino, "Cambia tu contraseña de Umbral", "Cambiar tu contraseña",
        [f"Hola, {nombre.split()[0]}. Recibimos una solicitud para cambiar la contraseña de tu cuenta.",
         f"El enlace sirve una sola vez y vence en {config.MINUTOS_RESTABLECER} minutos."],
        boton=("Elegir una contraseña nueva", f"{config.URL_SITIO}/restablecer?pase={token}"),
    )


def correo_aviso(destino: str, titulo: str, texto: str) -> bool:
    return enviar(destino, f"Umbral: {titulo}", titulo, [texto])
