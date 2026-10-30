# El corazon de Umbral: traduce un puerto tecnico a lenguaje sencillo.
# Para cada puerto conocido guardo que servicio es, que tan delicado es
# (nivel) y una explicacion y recomendacion que cualquiera pueda entender.
#
# niveles: "ok" (sin problemas), "revisar" (requiere revision), "importante".

CATALOGO = {
    21: {
        "servicio": "FTP",
        "nivel": "importante",
        "titulo": "Transferencia de archivos sin cifrar (FTP)",
        "explicacion": "Hay un servicio para enviar y recibir archivos por la red, pero sin proteger la informacion.",
        "riesgo": "Las contraseñas y los archivos viajan sin cifrar; alguien en la misma red podria verlos.",
        "recomendacion": "Si no lo usas, desactivalo. Si lo necesitas, cambia a una version segura (SFTP).",
    },
    22: {
        "servicio": "SSH",
        "nivel": "revisar",
        "titulo": "Acceso remoto al equipo (SSH)",
        "explicacion": "Permite entrar y controlar tu equipo desde otra computadora de forma segura.",
        "riesgo": "Si tu contraseña es debil, alguien podria intentar entrar probando contraseñas.",
        "recomendacion": "Deja esto abierto solo si de verdad lo usas, con una contraseña fuerte o llaves.",
    },
    23: {
        "servicio": "Telnet",
        "nivel": "importante",
        "titulo": "Acceso remoto inseguro (Telnet)",
        "explicacion": "Es una forma antigua de controlar el equipo a distancia, sin ningun cifrado.",
        "riesgo": "Todo, incluida tu contraseña, viaja a la vista de cualquiera en la red.",
        "recomendacion": "Desactivalo. Si necesitas acceso remoto, usa SSH en su lugar.",
    },
    25: {
        "servicio": "SMTP",
        "nivel": "revisar",
        "titulo": "Servidor de correo saliente (SMTP)",
        "explicacion": "Tu equipo tiene un servicio para enviar correos.",
        "riesgo": "Si no lo configuraste tu, podria estar siendo usado para mandar spam.",
        "recomendacion": "Si no sabes por que esta activo, conviene revisarlo o desactivarlo.",
    },
    53: {
        "servicio": "DNS",
        "nivel": "ok",
        "titulo": "Traductor de direcciones de internet (DNS)",
        "explicacion": "Ayuda a convertir nombres de paginas (como google.com) en direcciones de internet.",
        "riesgo": "En un equipo normal no suele representar un problema.",
        "recomendacion": "No necesitas hacer nada.",
    },
    80: {
        "servicio": "HTTP",
        "nivel": "revisar",
        "titulo": "Pagina web sin cifrar (HTTP)",
        "explicacion": "Hay un servidor web funcionando sin proteccion (sin candado https).",
        "riesgo": "La informacion que se envie por aqui viaja sin cifrar.",
        "recomendacion": "Si tienes un sitio, usa HTTPS. Si no sabes por que esta abierto, revisalo.",
    },
    110: {
        "servicio": "POP3",
        "nivel": "revisar",
        "titulo": "Recepcion de correo sin cifrar (POP3)",
        "explicacion": "Un servicio para descargar correos, en su version sin proteger.",
        "riesgo": "Tus credenciales de correo podrian viajar sin cifrar.",
        "recomendacion": "Usa la version segura del correo o desactiva este servicio.",
    },
    135: {
        "servicio": "MSRPC",
        "nivel": "revisar",
        "titulo": "Servicio interno de Windows (RPC)",
        "explicacion": "Windows lo usa para que programas se comuniquen entre si.",
        "riesgo": "No deberia estar accesible desde fuera de tu equipo.",
        "recomendacion": "Asegurate de tener activado el firewall de Windows.",
    },
    139: {
        "servicio": "NetBIOS",
        "nivel": "revisar",
        "titulo": "Compartir en red (NetBIOS)",
        "explicacion": "Parte del sistema antiguo de Windows para compartir archivos e impresoras.",
        "riesgo": "En redes publicas puede exponer informacion de tu equipo.",
        "recomendacion": "Desactiva el uso compartido cuando estes en redes publicas.",
    },
    143: {
        "servicio": "IMAP",
        "nivel": "revisar",
        "titulo": "Correo sin cifrar (IMAP)",
        "explicacion": "Un servicio para leer tu correo, en su version sin proteger.",
        "riesgo": "Tus credenciales podrian viajar sin cifrar.",
        "recomendacion": "Usa la version segura (IMAP con cifrado) o desactivalo.",
    },
    443: {
        "servicio": "HTTPS",
        "nivel": "ok",
        "titulo": "Pagina web segura (HTTPS)",
        "explicacion": "Hay un servidor web con conexion cifrada (el candado de seguridad).",
        "riesgo": "Es lo normal y recomendable para la web.",
        "recomendacion": "No necesitas hacer nada.",
    },
    445: {
        "servicio": "SMB",
        "nivel": "importante",
        "titulo": "Compartir archivos de Windows (SMB)",
        "explicacion": "Es el canal que Windows usa para compartir archivos e impresoras en una red.",
        "riesgo": "En redes publicas, alguien podria intentar entrar a tu equipo por aqui.",
        "recomendacion": "Desactiva el uso compartido en redes publicas y manten tu Windows actualizado.",
    },
    3306: {
        "servicio": "MySQL",
        "nivel": "importante",
        "titulo": "Base de datos MySQL",
        "explicacion": "Tienes una base de datos funcionando y aceptando conexiones.",
        "riesgo": "Si queda accesible desde internet, podrian intentar robar o dañar tus datos.",
        "recomendacion": "Permite que solo tu equipo (localhost) se conecte y usa una contraseña fuerte.",
    },
    3389: {
        "servicio": "RDP",
        "nivel": "importante",
        "titulo": "Escritorio remoto de Windows (RDP)",
        "explicacion": "Permite controlar tu equipo viendo su pantalla desde otra computadora.",
        "riesgo": "Es un objetivo muy comun de ataques si esta expuesto a internet.",
        "recomendacion": "Deja esto solo si lo usas, con contraseña fuerte, y de preferencia por VPN.",
    },
    5432: {
        "servicio": "PostgreSQL",
        "nivel": "importante",
        "titulo": "Base de datos PostgreSQL",
        "explicacion": "Tienes una base de datos PostgreSQL aceptando conexiones.",
        "riesgo": "Si queda abierta a internet, tus datos estarian en riesgo.",
        "recomendacion": "Limita el acceso a tu equipo (localhost) y usa una contraseña fuerte.",
    },
    8080: {
        "servicio": "HTTP alternativo",
        "nivel": "revisar",
        "titulo": "Servidor web de pruebas (puerto 8080)",
        "explicacion": "Suele ser un servidor web de desarrollo o un panel de administracion.",
        "riesgo": "Si no sabes que es, podria ser un programa expuesto sin querer.",
        "recomendacion": "Identifica que programa lo abrio; si no lo reconoces, cierralo.",
    },
}


def interpretar(puerto: int, servicio: str = ""):
    """Devuelve la explicacion en lenguaje sencillo para un puerto."""
    if puerto in CATALOGO:
        return CATALOGO[puerto]

    # Si no lo conozco, al menos devuelvo algo util y honesto.
    nombre = servicio or "desconocido"
    return {
        "servicio": nombre,
        "nivel": "revisar",
        "titulo": f"Servicio no identificado en el puerto {puerto}",
        "explicacion": "Encontramos un programa escuchando en este puerto, pero no lo tenemos en nuestro catalogo.",
        "riesgo": "No podemos decir si es peligroso sin saber que programa es.",
        "recomendacion": "Revisa que aplicacion esta usando este puerto; si no la reconoces, cierrala.",
    }
