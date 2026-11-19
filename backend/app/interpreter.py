# El corazon de Umbral: convierte un puerto abierto en una explicacion que
# entiende cualquiera. La idea central es la casa: tu computadora tiene
# 65,535 puertas numeradas y cada programa que espera conexiones abre una.
#
# Niveles (los mismos tres en toda la app):
#   tranquilo -> normal, no hay que hacer nada
#   atento    -> no es grave, pero conviene saber por que esta abierta
#   urgente   -> cierrala o protegela cuanto antes
#
# El nivel cambia segun el alcance:
#   "red"     -> la puerta da a la calle: otros equipos de la red pueden tocarla
#   "interno" -> la puerta da a un pasillo interior: solo tu propia computadora la usa
import json
import re


def _p(servicio, puerta, que, riesgo, red, interno="tranquilo", win=(), lin=()):
    return {"servicio": servicio, "puerta": puerta, "que": que, "riesgo": riesgo,
            "red": red, "interno": interno, "windows": list(win), "linux": list(lin)}


_SERVICIOS_WIN = "Presiona Windows + R, escribe services.msc y pulsa Enter."

CATALOGO = {
    20: _p("FTP (datos)", "Envío de archivos sin protección",
           "Es la segunda puerta que usa FTP, un sistema antiguo para pasar archivos entre computadoras.",
           "Lo que pasa por aquí viaja sin cifrar: quien esté en tu misma red puede copiarlo.", "urgente", "atento",
           win=["Abre Panel de control > Programas > Activar o desactivar las características de Windows.",
                "Desmarca «Servidor FTP» dentro de Internet Information Services y acepta."],
           lin=["Mira qué programa lo abrió: sudo ss -tulpn | grep ':20 '",
                "Si es vsftpd y no lo usas: sudo systemctl disable --now vsftpd"]),
    21: _p("FTP", "Envío de archivos sin protección",
           "Tu equipo está ofreciendo sus archivos por FTP, un sistema de los años 70 para pasar archivos por la red.",
           "Usuario, contraseña y archivos viajan como texto a la vista. En una red compartida (escuela, café) cualquiera con un programa gratuito puede leerlos.",
           "urgente", "atento",
           win=["Abre Panel de control > Programas > Activar o desactivar las características de Windows.",
                "Desmarca «Servidor FTP» dentro de Internet Information Services y acepta.",
                "Si usas FileZilla Server u otro programa, ciérralo y quítalo del inicio."],
           lin=["Apágalo y evita que vuelva a encender: sudo systemctl disable --now vsftpd",
                "Si necesitas pasar archivos, usa SFTP (va por la puerta 22 y sí cifra)."]),
    22: _p("SSH", "Control remoto por terminal",
           "Permite que alguien escriba comandos en tu computadora desde otra, con la conexión cifrada. Es la herramienta normal de quien administra servidores.",
           "Es seguro por diseño, pero si tu contraseña es corta, hay programas que prueban miles por minuto hasta entrar.",
           "atento",
           win=["Si no lo usas: Configuración > Sistema > Características opcionales, busca «Servidor OpenSSH» y desinstálalo.",
                "Si lo usas, entra con llaves en lugar de contraseña."],
           lin=["Si no lo usas: sudo systemctl disable --now ssh",
                "Si lo usas: en /etc/ssh/sshd_config pon PasswordAuthentication no y PermitRootLogin no, y reinicia con sudo systemctl restart ssh"]),
    23: _p("Telnet", "Control remoto sin candado",
           "Es el abuelo del control remoto: deja manejar tu equipo a distancia, pero sin ninguna protección.",
           "Todo lo que se escribe, incluida la contraseña, cruza la red como una postal sin sobre. Hoy casi no hay razón legítima para tenerlo abierto.",
           "urgente", "atento",
           win=["Abre Panel de control > Programas > Activar o desactivar las características de Windows.",
                "Desmarca «Servidor Telnet» (y «Cliente Telnet» si no lo usas)."],
           lin=["sudo systemctl disable --now telnet.socket inetd xinetd 2>/dev/null",
                "Desinstálalo: sudo apt remove telnetd"]),
    25: _p("SMTP", "Buzón para enviar correo",
           "Tu equipo tiene encendido un servicio que envía correos, como una pequeña oficina postal.",
           "Si no lo instalaste tú, alguien podría usar tu computadora para mandar spam y tu conexión acabaría en listas negras.",
           "atento",
           win=[_SERVICIOS_WIN, "Busca «SMTP» o «Simple Mail Transfer Protocol», clic derecho > Detener y luego Propiedades > Tipo de inicio: Deshabilitado."],
           lin=["Mira cuál es: sudo ss -tulpn | grep ':25 '",
                "Si es postfix o exim y no lo ocupas: sudo systemctl disable --now postfix exim4"]),
    53: _p("DNS", "Directorio de internet",
           "Convierte nombres como google.com en las direcciones numéricas que usan las computadoras. Es la agenda telefónica de internet.",
           "En una computadora personal casi siempre es parte normal del sistema.", "atento",
           win=["Normalmente lo abre «Conexión compartida a Internet» o un programa de máquinas virtuales. Si no compartes tu internet, puedes dejarlo así."],
           lin=["En Linux lo abre systemd-resolved o dnsmasq para tu propia máquina. No necesitas hacer nada."]),
    67: _p("DHCP", "Reparto de direcciones", "Reparte direcciones a los dispositivos que se conectan a una red. Lo usan los módems y los programas de máquinas virtuales.",
           "Normal si usas máquinas virtuales o compartes tu internet.", "tranquilo"),
    68: _p("DHCP", "Pedir dirección a la red", "Es la puerta por la que tu equipo recibe su dirección cuando se conecta al Wi-Fi.",
           "Es parte normal de conectarse a cualquier red.", "tranquilo"),
    80: _p("HTTP", "Página web sin candado",
           "Hay un servidor web funcionando en tu equipo: algo en tu computadora está mostrando una página.",
           "Sin el candado (https) lo que se envíe a esa página viaja sin cifrar. Y si no sabías que existía, hay un programa publicando algo sin avisarte.",
           "atento",
           win=["Averigua qué programa es: en el Administrador de tareas > pestaña Detalles busca el nombre que aparece arriba.",
                "Si es IIS y no lo usas: Panel de control > Activar o desactivar las características de Windows > desmarca Internet Information Services."],
           lin=["Mira cuál es: sudo ss -tulpn | grep ':80 '",
                "Si es apache2 o nginx y no lo usas: sudo systemctl disable --now apache2 nginx"]),
    110: _p("POP3", "Buzón de correo sin candado", "Un servicio para descargar correos, en su versión sin cifrar.",
            "El usuario y la contraseña del correo viajan a la vista.", "atento",
            lin=["Si es dovecot y no lo usas: sudo systemctl disable --now dovecot"]),
    111: _p("RPCbind", "Recepcionista de servicios", "Es un recepcionista que le dice a otros equipos en qué puerta atiende cada servicio de red de Linux (sobre todo carpetas compartidas NFS).",
            "Le da a un curioso el mapa de lo que ofrece tu equipo. Se ha usado además para ataques que saturan a otros.", "atento",
            lin=["Si no compartes carpetas por NFS: sudo systemctl disable --now rpcbind rpcbind.socket"]),
    123: _p("NTP", "Reloj de internet", "Mantiene la hora de tu equipo sincronizada.", "Es normal y necesario.", "tranquilo"),
    135: _p("RPC de Windows", "Recepcionista de Windows",
            "Es el recepcionista interno de Windows: los programas le preguntan dónde encontrar otros servicios del sistema. Viene encendido de fábrica.",
            "No se puede apagar sin romper Windows. Lo que importa es que tu cortafuegos esté encendido para que no lo alcancen desde fuera.",
            "atento",
            win=["Abre Seguridad de Windows > Firewall y protección de red y confirma que las tres redes digan «Activado».",
                 "En redes que no son tuyas (escuela, café) elige el perfil «Red pública»."]),
    137: _p("NetBIOS", "Nombre del equipo en la red", "Anuncia el nombre de tu computadora a los demás equipos de la red local. Es un sistema viejo de Windows.",
            "Revela el nombre de tu equipo y facilita engaños dentro de la red.", "atento",
            win=["Panel de control > Redes > Cambiar configuración del adaptador > clic derecho en tu red > Propiedades.",
                 "IPv4 > Propiedades > Opciones avanzadas > pestaña WINS > «Deshabilitar NetBIOS sobre TCP/IP»."]),
    138: _p("NetBIOS", "Nombre del equipo en la red", "Parte del sistema viejo con el que Windows se anuncia en la red local.",
            "Revela información de tu equipo a quien comparta red contigo.", "atento",
            win=["Igual que la puerta 137: desactiva NetBIOS sobre TCP/IP en las propiedades avanzadas de IPv4."]),
    139: _p("NetBIOS", "Carpetas compartidas (versión antigua)",
            "Es la puerta vieja por la que Windows comparte carpetas e impresoras con otros equipos.",
            "Si alguna carpeta quedó compartida sin contraseña, cualquiera en tu red puede abrirla.", "urgente", "atento",
            win=["Configuración > Red e Internet > Configuración de uso compartido avanzado.",
                 "En «Redes públicas» apaga «Uso compartido de archivos e impresoras».",
                 "Además desactiva NetBIOS sobre TCP/IP (ver puerta 137)."],
            lin=["Si es Samba y no compartes carpetas: sudo systemctl disable --now smbd nmbd"]),
    143: _p("IMAP", "Buzón de correo sin candado", "Un servicio para leer correos desde otros dispositivos, sin cifrar.",
            "La contraseña del correo viaja a la vista.", "atento",
            lin=["Si es dovecot y no lo usas: sudo systemctl disable --now dovecot"]),
    443: _p("HTTPS", "Página web con candado",
            "Hay un servidor web con conexión cifrada funcionando en tu equipo.",
            "La conexión es segura, pero conviene saber qué programa está publicando una página desde tu computadora.", "atento",
            win=["Revisa en el Administrador de tareas qué programa aparece arriba. Suele ser una app de trabajo, VMware o Skype."],
            lin=["Mira cuál es: sudo ss -tulpn | grep ':443 '"]),
    445: _p("SMB", "Carpetas compartidas de Windows",
            "Por aquí Windows comparte carpetas e impresoras con otras computadoras de la red.",
            "Es la puerta que usó el virus WannaCry en 2017 para secuestrar los archivos de más de 200 mil equipos. En tu casa suele ser inofensiva; en una red pública es una invitación.",
            "urgente", "atento",
            win=["Instala todas las actualizaciones: Configuración > Windows Update > Buscar actualizaciones.",
                 "Configuración > Red e Internet > Configuración de uso compartido avanzado: apaga «Uso compartido de archivos e impresoras» en Redes públicas.",
                 "Si nunca compartes carpetas, apágalo también en Redes privadas."],
            lin=["Si es Samba y no compartes carpetas: sudo systemctl disable --now smbd",
                 "Si lo usas, exige contraseña en /etc/samba/smb.conf (map to guest = never)."]),
    515: _p("LPD", "Impresión en red", "Servicio antiguo para recibir trabajos de impresión.", "Rara vez se necesita hoy.", "atento"),
    631: _p("CUPS", "Sistema de impresión", "Es el sistema de impresoras de Linux y Mac. Tiene una página de control en esta puerta.",
            "Si está abierto a la red, otros podrían ver o administrar tus impresoras. Ha tenido fallas graves cuando queda expuesto.", "atento",
            lin=["Si no imprimes: sudo systemctl disable --now cups cups-browsed",
                 "Si imprimes, deja que escuche solo en tu equipo: en /etc/cups/cupsd.conf usa Listen localhost:631"]),
    1433: _p("SQL Server", "Base de datos de Microsoft", "Hay una base de datos SQL Server esperando conexiones.",
             "Las bases de datos guardan lo más valioso. Abiertas a la red, reciben intentos constantes de adivinar la contraseña.", "urgente",
             win=["Abre «Administrador de configuración de SQL Server» > Configuración de red > Protocolos.",
                  "Deshabilita TCP/IP si solo la usas desde tu propio equipo y reinicia el servicio."]),
    1900: _p("SSDP / UPnP", "Descubrimiento de dispositivos", "Sirve para que tu equipo encuentre televisores, consolas e impresoras en la red sin configurar nada.",
             "Cómodo en casa. En redes ajenas anuncia tu equipo a desconocidos.", "atento",
             win=[_SERVICIOS_WIN, "Busca «Detección SSDP», clic derecho > Detener y en Propiedades pon Tipo de inicio: Deshabilitado."]),
    2049: _p("NFS", "Carpetas compartidas de Linux", "Comparte carpetas entre equipos Linux.",
             "Mal configurado, deja leer o modificar archivos a cualquiera de la red.", "urgente", "atento",
             lin=["Si no compartes carpetas: sudo systemctl disable --now nfs-server"]),
    3000: _p("Servidor de desarrollo", "Proyecto web en construcción", "Suele ser un proyecto de programación corriendo (Node, React, Grafana).",
             "Los servidores de desarrollo no están hechos para aguantar ataques; no deberían verse desde otros equipos.", "atento",
             win=["Si ya no trabajas en el proyecto, cierra la terminal donde corre."],
             lin=["Si ya no trabajas en el proyecto, cierra la terminal donde corre (Ctrl + C)."]),
    3306: _p("MySQL / MariaDB", "Base de datos",
             "Hay una base de datos MySQL o MariaDB encendida. Es donde los sistemas guardan usuarios, ventas, calificaciones.",
             "Abierta a la red, cualquiera puede intentar adivinar la contraseña. Muchas instalaciones de práctica (XAMPP) dejan al usuario root sin contraseña.",
             "urgente",
             win=["Si usas XAMPP o WAMP, abre su panel y detén MySQL cuando no estés trabajando.",
                  "Para que solo tu equipo la use: en my.ini agrega bind-address=127.0.0.1 y reinicia MySQL.",
                  "Ponle contraseña al usuario root."],
             lin=["Para que solo tu equipo la use: en /etc/mysql/mariadb.conf.d/50-server.cnf pon bind-address = 127.0.0.1",
                  "Reinicia: sudo systemctl restart mariadb",
                  "Si no la usas: sudo systemctl disable --now mariadb mysql"]),
    3389: _p("Escritorio remoto (RDP)", "Control remoto de Windows",
             "Permite ver tu pantalla y mover tu mouse desde otra computadora, como si estuvieran sentados frente a ella.",
             "Es de las puertas más atacadas del mundo: hay programas que recorren internet buscándola y probando contraseñas. Muchos secuestros de archivos (ransomware) empiezan aquí.",
             "urgente",
             win=["Configuración > Sistema > Escritorio remoto.", "Apaga el interruptor «Escritorio remoto».",
                  "Si de verdad lo necesitas, usa una contraseña larga y actívalo solo mientras lo ocupas."],
             lin=["Si es xrdp y no lo usas: sudo systemctl disable --now xrdp"]),
    5000: _p("Servidor de desarrollo", "Proyecto web en construcción", "Suele ser un proyecto en Flask u otra herramienta de programación.",
             "No está pensado para quedar a la vista de otros equipos.", "atento",
             win=["Cierra la terminal donde corre si ya no lo usas."], lin=["Cierra la terminal donde corre (Ctrl + C)."]),
    5040: _p("Servicio de Windows", "Conexión de dispositivos", "Lo usa Windows para conectar dispositivos y plataformas.", "Parte normal del sistema.", "tranquilo"),
    5173: _p("Vite", "Proyecto web en construcción", "Es un proyecto web en desarrollo (por ejemplo, el propio Umbral mientras lo programas).",
             "Solo debería estar encendido mientras trabajas en él.", "atento", lin=["Se cierra con Ctrl + C en su terminal."], win=["Se cierra con Ctrl + C en su terminal."]),
    5353: _p("mDNS", "Descubrimiento en red local", "Ayuda a encontrar impresoras, televisores y otros equipos por su nombre dentro de tu red.",
             "Normal en redes de casa. En redes ajenas anuncia el nombre de tu equipo.", "tranquilo"),
    5355: _p("LLMNR", "Nombres en red local", "Otra forma en que Windows busca equipos por nombre en la red local.",
             "En redes compartidas se usa para engañar a tu equipo y robar la contraseña cifrada de tu sesión.", "atento",
             win=["Presiona Windows + R, escribe gpedit.msc (solo ediciones Pro).",
                  "Configuración del equipo > Plantillas administrativas > Red > Cliente DNS > «Desactivar resolución de nombres de multidifusión»: Habilitada."]),
    5432: _p("PostgreSQL", "Base de datos", "Hay una base de datos PostgreSQL encendida.",
             "Abierta a la red recibe intentos de adivinar la contraseña y, si cede, se llevan todos los datos.", "urgente",
             win=["En postgresql.conf deja listen_addresses = 'localhost' y reinicia el servicio postgresql desde services.msc."],
             lin=["En /etc/postgresql/*/main/postgresql.conf deja listen_addresses = 'localhost'", "sudo systemctl restart postgresql"]),
    5900: _p("VNC", "Pantalla compartida",
             "Deja ver y controlar tu pantalla desde otro equipo.",
             "Muchas instalaciones no cifran la conexión y aceptan contraseñas de 8 letras. Hay buscadores públicos que listan miles de pantallas VNC abiertas.",
             "urgente", "atento",
             win=["Cierra el programa de VNC (TightVNC, RealVNC, UltraVNC) y quítalo del inicio si no lo ocupas."],
             lin=["Mira cuál es: sudo ss -tulpn | grep ':5900'", "Detén el servidor VNC que aparezca (por ejemplo: vncserver -kill :0)."]),
    5985: _p("WinRM", "Administración remota de Windows", "Permite administrar Windows a distancia con comandos.",
             "Con una contraseña robada, da control total del equipo.", "urgente",
             win=["Abre PowerShell como administrador y ejecuta: Disable-PSRemoting -Force", "Luego: Stop-Service WinRM; Set-Service WinRM -StartupType Disabled"]),
    6379: _p("Redis", "Base de datos en memoria", "Es una base de datos rápida que usan los programadores.",
             "De fábrica no pide contraseña: abierta a la red, cualquiera la lee o la borra.", "urgente",
             lin=["En /etc/redis/redis.conf deja bind 127.0.0.1 y activa requirepass con una contraseña.", "sudo systemctl restart redis-server"]),
    7680: _p("Optimización de distribución", "Reparto de actualizaciones",
             "Windows la usa para compartir pedazos de sus actualizaciones con otros equipos y descargarlas más rápido.",
             "No es peligrosa, aunque gasta tu internet en ayudar a otros.", "tranquilo",
             win=["Opcional: Configuración > Windows Update > Opciones avanzadas > Optimización de distribución > apaga «Permitir descargas de otros equipos»."]),
    8000: _p("Servidor de desarrollo", "Proyecto web en construcción", "Suele ser una API o página en desarrollo (por ejemplo, la API de Umbral).",
             "Solo debería estar encendido mientras trabajas en él.", "atento", win=["Se cierra con Ctrl + C en su terminal."], lin=["Se cierra con Ctrl + C en su terminal."]),
    8080: _p("Web alterna / proxy", "Página web secundaria", "Una segunda puerta para páginas web. La usan servidores de práctica, cámaras y herramientas como Burp Suite.",
             "Conviene saber qué programa publica algo ahí.", "atento",
             win=["Revisa en el Administrador de tareas qué programa es y ciérralo si no lo reconoces."],
             lin=["Mira cuál es: sudo ss -tulpn | grep ':8080'"]),
    8443: _p("Web segura alterna", "Página web secundaria", "Otra puerta para páginas con candado, común en paneles de administración.",
             "Los paneles de administración son un blanco favorito.", "atento"),
    9050: _p("Tor", "Navegación anónima", "Es la puerta del programa Tor, que oculta tu ubicación al navegar.",
             "Es legítimo si tú lo instalaste. Si no, alguien lo puso para ocultar actividad.", "atento"),
    27017: _p("MongoDB", "Base de datos", "Hay una base de datos MongoDB encendida.",
              "Miles de bases MongoDB han sido vaciadas y secuestradas por quedar abiertas sin contraseña.", "urgente",
              lin=["En /etc/mongod.conf deja bindIp: 127.0.0.1", "sudo systemctl restart mongod"],
              win=["En mongod.cfg deja bindIp: 127.0.0.1 y reinicia el servicio MongoDB desde services.msc."]),
}

# Puertas que los programas legitimos casi nunca usan y las herramientas de
# ataque si. Verlas abiertas no prueba una infeccion, pero merece revision ya.
SOSPECHOSOS = {
    1337: "Es un número que la cultura hacker usa como firma («leet»). Aparece en puertas traseras caseras.",
    4444: "Es la puerta que usa de fábrica Metasploit, la herramienta de ataque más conocida, para controlar un equipo ya comprometido.",
    4445: "Variante de la 4444, usada por herramientas de control remoto oculto.",
    5554: "La usó el gusano Sasser y la usan algunos troyanos.",
    6666: "Asociada a troyanos y a redes de equipos controlados (botnets).",
    6667: "Es la puerta del chat IRC. Muchos equipos infectados la usan para recibir órdenes.",
    9001: "La usa Tor para enlazar equipos. Si no instalaste Tor, alguien más lo hizo.",
    12345: "La hizo famosa NetBus, uno de los primeros troyanos de control remoto.",
    27374: "Puerta del troyano SubSeven.",
    31337: "Puerta del troyano Back Orifice; el número se lee «eleet» (élite).",
    54321: "Usada por troyanos como School Bus y Back Orifice 2000.",
}

# Programas comunes: nombre que aparece en el proceso -> como explicarlo.
PROGRAMAS = [
    (r"spotify", "Spotify", "Spotify la abre para que tu celular pueda controlar la música de la computadora."),
    (r"discord", "Discord", "Discord la abre para sus funciones de voz y para avisarle al sistema qué juegas."),
    (r"steam", "Steam", "Steam la abre para descargas, juego remoto y transferencias entre equipos de tu red."),
    (r"chrome|msedge|firefox|brave|opera", "tu navegador", "El navegador la abre para funciones como enviar pestañas a la tele (Cast) o videollamadas."),
    (r"code|electron", "Visual Studio Code", "El editor la abre para comunicarse con sus extensiones."),
    (r"docker|com\.docker|vpnkit", "Docker", "Docker la abre para los contenedores que tienes corriendo."),
    (r"vmware|vbox|virtualbox|vmms|qemu", "tu programa de máquinas virtuales", "La abre el programa con el que corres máquinas virtuales."),
    (r"teams|zoom|skype|webex", "tu app de videollamadas", "La app de videollamadas la abre para audio y video."),
    (r"onedrive|dropbox|googledrive|megasync", "tu app de nube", "La app que sincroniza tus archivos la abre para encontrar otros equipos tuyos en la red."),
    (r"nvidia|nvcontainer|amd|radeon", "el controlador de tu tarjeta de video", "El software de tu tarjeta gráfica la abre para sus funciones de grabación y transmisión."),
    (r"python|uvicorn|node|java|php|ruby|dotnet", "un programa en desarrollo", "La abrió un programa hecho en un lenguaje de programación; suele ser un proyecto que alguien dejó corriendo."),
    (r"anydesk|teamviewer|rustdesk|ammyy|supremo", "un programa de control remoto",
     "Es un programa que deja manejar tu equipo a distancia. Es la herramienta favorita de los estafadores que se hacen pasar por soporte técnico."),
    (r"gophish|mailpit|burp|msf|metasploit|nc\.exe|ncat|netcat|socat", "una herramienta de pruebas de seguridad",
     "La abrió una herramienta de seguridad. Normal si estás haciendo una práctica; preocupante si no la instalaste tú."),
    (r"svchost|lsass|wininit|services|spoolsv|system|smss|csrss", "Windows", "La abrió el propio Windows para sus servicios internos."),
    (r"systemd|avahi|cupsd|networkmanager|dhclient|chronyd|rpc", "el sistema", "La abrió el propio sistema operativo para sus servicios de red."),
]
# Programas de uso diario: su puerta abierta es parte de como funcionan.
_DE_CONFIANZA = {"Spotify", "Discord", "Steam", "tu navegador", "Visual Studio Code", "tu app de videollamadas",
                 "tu app de nube", "el controlador de tu tarjeta de video"}
_CONTROL_REMOTO = re.compile(r"anydesk|teamviewer|rustdesk|ammyy|supremo", re.I)
_CARPETA_RARA = re.compile(r"(\\temp\\|\\tmp\\|/tmp/|/dev/shm/|\\downloads\\|/descargas/|/downloads/|\\appdata\\local\\temp)", re.I)
_SISTEMA_WIN = re.compile(r"^(svchost|lsass|wininit|services|spoolsv|system)(\.exe)?$", re.I)

ORDEN_NIVEL = {"urgente": 0, "atento": 1, "tranquilo": 2}


def _pasos_genericos(proceso):
    quien = f"«{proceso}»" if proceso else "el programa que la abrió"
    return {
        "windows": [f"Abre el Administrador de tareas (Ctrl + Shift + Esc) > pestaña Detalles y busca {quien}.",
                    "Clic derecho > «Abrir ubicación del archivo» para ver de qué programa es.",
                    "Si no lo reconoces o no lo usas, desinstálalo desde Configuración > Aplicaciones."],
        "linux": ["Mira qué programa la tiene abierta: sudo ss -tulpn",
                  f"Si no reconoces a {quien}, búscalo: ps aux | grep -i " + (proceso or "nombre"),
                  "Si es un servicio que no usas: sudo systemctl disable --now nombre-del-servicio"],
    }


def interpretar(item: dict) -> dict:
    """Recibe un puerto tal como lo reporta el agente y devuelve la explicacion completa."""
    puerto = int(item["puerto"])
    alcance = item.get("alcance", "red")
    proceso = (item.get("proceso") or "").strip()
    ruta = (item.get("ruta") or "").strip()
    senales = []

    conocido = CATALOGO.get(puerto)
    programa = next((p for p in PROGRAMAS if proceso and re.search(p[0], proceso, re.I)), None)

    if puerto in SOSPECHOSOS:
        servicio, titulo = "Puerta sospechosa", f"Puerta {puerto}: úsala como señal de alarma"
        explicacion = SOSPECHOSOS[puerto]
        riesgo = "Si tú no abriste esto para una práctica, puede haber un programa dando acceso a tu equipo a otra persona."
        nivel = "urgente" if alcance == "red" else "atento"
        pasos = _pasos_genericos(proceso)
        for so in pasos:
            pasos[so].append("Pasa un análisis completo con tu antivirus (en Windows: Seguridad de Windows > Protección contra virus > Examen completo).")
    elif conocido:
        servicio, titulo = conocido["servicio"], conocido["puerta"]
        explicacion, riesgo = conocido["que"], conocido["riesgo"]
        nivel = conocido["red"] if alcance == "red" else conocido["interno"]
        genericos = _pasos_genericos(proceso)
        pasos = {so: (conocido[so] or genericos[so]) for so in ("windows", "linux")}
    elif programa:
        servicio, titulo = programa[1].capitalize() if programa[1][0].islower() else programa[1], f"Abierta por {programa[1]}"
        explicacion = programa[2]
        riesgo = "Mientras el programa esté actualizado no suele ser un problema. Si no lo usas, ciérralo y la puerta se cierra con él."
        nivel = "tranquilo" if alcance == "interno" or programa[1] in _DE_CONFIANZA else "atento"
        if _SISTEMA_WIN.match(proceso) or programa[1] in ("Windows", "el sistema"):
            nivel = "tranquilo"
            riesgo = "Es parte del funcionamiento normal del sistema. Tu cortafuegos es quien evita que la toquen desde fuera."
        pasos = _pasos_genericos(proceso)
    else:
        servicio = "Sin identificar"
        titulo = f"Puerta {puerto} sin dueño conocido"
        explicacion = (f"El programa «{proceso}» abrió esta puerta y no está en el catálogo de Umbral." if proceso else
                       "Algo abrió esta puerta y no pudimos ver qué programa fue.")
        riesgo = "No significa que sea malo: hay miles de programas legítimos. Pero una puerta abierta de la que no sabes nada merece dos minutos de revisión."
        nivel = "atento" if alcance == "red" else "tranquilo"
        pasos = _pasos_genericos(proceso)

    # Señales extra que suben la atencion sin importar el puerto
    if _CONTROL_REMOTO.search(proceso):
        nivel = "urgente" if alcance == "red" else "atento"
        riesgo = "Quien tenga el código de acceso maneja tu equipo completo: ve tu pantalla, abre tu banco, copia tus archivos. Déjalo instalado solo si tú lo usas."
        senales.append("Es un programa de control remoto. Si alguien te pidió instalarlo por teléfono o chat «para ayudarte», desinstálalo ya.")
    if ruta and _CARPETA_RARA.search(ruta):
        nivel = "urgente"
        senales.append("El programa se ejecuta desde una carpeta temporal o de descargas. Los programas instalados correctamente no viven ahí; el malware sí.")
    if not proceso:
        senales.append("No pudimos ver qué programa la abrió. Ejecuta el agente como administrador para saberlo.")
    if alcance == "interno":
        senales.append("Solo tu propia computadora puede usar esta puerta; otros equipos no la alcanzan.")

    return {
        "servicio": servicio[:60], "titulo": titulo[:140], "explicacion": explicacion, "riesgo": riesgo,
        "nivel": nivel, "pasos": json.dumps(pasos, ensure_ascii=False), "senales": json.dumps(senales, ensure_ascii=False),
    }


def ficha_publica(puerto: int) -> dict:
    """Para el buscador «¿Que es el puerto X?» de la seccion Aprende."""
    if puerto in SOSPECHOSOS:
        return {"puerto": puerto, "servicio": "Puerta sospechosa", "titulo": f"Puerta {puerto}",
                "explicacion": SOSPECHOSOS[puerto], "riesgo": "Verla abierta sin haberla abierto tú es motivo para revisar el equipo.",
                "nivel": "urgente", "conocido": True}
    c = CATALOGO.get(puerto)
    if c:
        return {"puerto": puerto, "servicio": c["servicio"], "titulo": c["puerta"], "explicacion": c["que"],
                "riesgo": c["riesgo"], "nivel": c["red"], "conocido": True}
    if puerto >= 49152:
        texto = "Está en el rango de puertas temporales (49152 a 65535). Los programas las toman prestadas un rato y las sueltan."
    elif puerto >= 1024:
        texto = "Está en el rango de puertas registradas (1024 a 49151), las que usan los programas que instalas."
    else:
        texto = "Está en el rango de puertas reservadas (0 a 1023), las de los servicios clásicos de internet."
    return {"puerto": puerto, "servicio": "Sin ficha", "titulo": f"Puerta {puerto}", "explicacion": texto,
            "riesgo": "Umbral no tiene una ficha para este número. Lo que importa es qué programa la abrió: eso te lo dice una revisión.",
            "nivel": "atento", "conocido": False}
