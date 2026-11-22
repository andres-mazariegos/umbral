# Guía paso a paso

Pensada para alguien que nunca ha levantado un proyecto. Sigue los pasos en
orden; cada uno dice qué deberías ver para saber que salió bien.

- [1. Instalar lo necesario](#1-instalar-lo-necesario)
- [2. Encender Umbral](#2-encender-umbral)
- [3. Crear tu cuenta](#3-crear-tu-cuenta)
- [4. Hacer tu primera revisión](#4-hacer-tu-primera-revisión)
- [5. Que el correo llegue de verdad](#5-que-el-correo-llegue-de-verdad)
- [6. Abrirlo desde el celular](#6-abrirlo-desde-el-celular)
- [7. Correr las pruebas](#7-correr-las-pruebas)
- [8. Publicarlo con un dominio (opcional)](#8-publicarlo-con-un-dominio-opcional)
- [Si algo falla](#si-algo-falla)

---

## 1. Instalar lo necesario

Umbral necesita dos programas: **Python** (para la API y el agente) y
**Node.js** (para construir el sitio).

### En Kali Linux

Abre una terminal y pega:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm
```

Comprueba:

```bash
python3 --version
node --version
```

Deben aparecer dos números de versión (Python 3.11 o mayor, Node 20 o mayor).

### En Windows

1. Entra a <https://www.python.org/downloads/>, descarga Python y, **en la
   primera pantalla del instalador, marca «Add python.exe to PATH»**. Luego
   «Install Now».
2. Entra a <https://nodejs.org/>, descarga la versión **LTS** e instálala con
   todo por defecto.
3. Cierra y vuelve a abrir PowerShell. Comprueba:

```powershell
python --version
node --version
```

---

## 2. Encender Umbral

Abre la terminal **dentro de la carpeta del proyecto** (la que tiene
`iniciar.sh`, `backend`, `frontend`).

### En Kali Linux

```bash
chmod +x iniciar.sh
./iniciar.sh
```

### En Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\iniciar.ps1
```

La primera línea solo le da permiso a esa ventana de PowerShell para correr el
script; no cambia nada permanente.

**Qué deberías ver:** la primera vez tarda unos minutos instalando. Al final:

```
   Abre en tu navegador:   http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Deja esa ventana abierta: ahí vive Umbral. Para apagarlo, `Ctrl + C`.

---

## 3. Crear tu cuenta

1. Abre <http://localhost:8000> y pulsa **Revisar mi computadora**.
2. Escribe tu nombre (solo acepta letras), tu correo y una contraseña de 10
   caracteres o más con mayúsculas, minúsculas y un número.
3. Umbral te pide un **código de 6 números**.
   - Si todavía no configuras el correo (paso 5), el código aparece en la misma
     pantalla con la leyenda «Modo desarrollo» y también en la ventana de la
     terminal.
   - Con el correo configurado, llega a tu bandeja.
4. Escribe el código. Entras directo al panel.

---

## 4. Hacer tu primera revisión

Tienes tres formas, de la más rápida a la más completa:

**a) Revisar este equipo ahora.** Como Umbral corre en tu propia computadora,
el botón del panel la revisa al instante.

**b) Ver un ejemplo.** Abre una revisión de muestra (una laptop descuidada con
varias sorpresas). Sirve para enseñar el proyecto sin depender de lo que tenga
abierto tu equipo ese día.

**c) Con el agente** (la forma real, para cualquier computadora):

1. En el panel entra a **Equipos > Conectar un equipo**.
2. Ponle nombre, marca las tres casillas de permiso y pulsa **Doy mi permiso**.
3. Umbral te muestra un código como `K7QM-2XRD` y los comandos exactos.
4. Descarga el agente con el botón: `umbral-agente.ps1` si es Windows o
   `umbral_agente.py` si es Kali/Linux.
5. En la computadora que quieres revisar abre una terminal en la carpeta de
   descargas y pega el comando que te da la pantalla. Por ejemplo:

   ```bash
   # Kali o cualquier Linux (Python ya viene instalado)
   cd ~/Downloads
   sudo python3 umbral_agente.py --servidor https://umbral.mazariegoscarlos.com --codigo K7QM-2XRD
   ```
   ```powershell
   # Windows (no hay que instalar nada)
   cd $HOME\Downloads
   powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1 -Servidor https://umbral.mazariegoscarlos.com -Codigo K7QM-2XRD
   ```
6. El agente te pregunta en pantalla si le das permiso. Responde `s`.
7. La página del navegador cambia sola a «ya está conectado». Abre la revisión.

Para revisar otra vez ese equipo ya no hace falta código:

| Sistema | Comando |
|---|---|
| Kali / Linux | `sudo python3 umbral_agente.py` |
| Windows | `powershell -ExecutionPolicy Bypass -File .\umbral-agente.ps1` |

Otras opciones del agente:

| Linux | Windows | Qué hace |
|---|---|---|
| `--ver` | `-Ver` | Muestra lo que enviaría, sin enviar nada |
| `--vigilar 30` | `-Vigilar 30` | Revisa cada 30 minutos |
| `--olvidar` | `-Olvidar` | Borra la conexión guardada en ese equipo |

> `-ExecutionPolicy Bypass` solo vale para esa ejecución: no cambia la
> seguridad de Windows. Para que el agente vea **todos** los programas, abre
> PowerShell con clic derecho > «Ejecutar como administrador» (en Linux, `sudo`).

---

## 5. Que el correo llegue de verdad

Sin configurar nada, los correos solo se muestran en la terminal. Para que
lleguen a una bandeja real se usa una cuenta de Gmail como remitente.

1. Entra a <https://myaccount.google.com/security> con la cuenta de Gmail que
   enviará los correos y activa la **Verificación en 2 pasos**.
2. Entra a <https://myaccount.google.com/apppasswords>, escribe el nombre
   «Umbral» y pulsa **Crear**. Google te da una contraseña de 16 letras.
   Cópiala (sin espacios).
3. En la carpeta `backend`, copia el archivo `.env.example` y nómbralo `.env`:

   ```bash
   cp backend/.env.example backend/.env        # Kali
   ```
   ```powershell
   Copy-Item backend\.env.example backend\.env  # Windows
   ```
4. Abre `backend/.env` con un editor de texto y llena estas líneas:

   ```
   UMBRAL_SMTP_HOST=smtp.gmail.com
   UMBRAL_SMTP_PORT=587
   UMBRAL_SMTP_USER=tucorreo@gmail.com
   UMBRAL_SMTP_PASS=las16letrasquetediogoogle
   UMBRAL_CORREO_REMITENTE=tucorreo@gmail.com
   ```
5. Apaga Umbral (`Ctrl + C`) y vuelve a encenderlo.
6. Regístrate con otro correo: el código debe llegar en unos segundos. Si no lo
   ves, revisa la carpeta de spam.

El archivo `.env` contiene una contraseña: **nunca lo subas a GitHub**. Ya está
en `.gitignore` para que Git lo ignore.

**Alternativa para la exposición sin internet:** Mailpit (el que usaste en la
práctica de GoPhish). Enciéndelo y pon en `.env`:

```
UMBRAL_SMTP_HOST=127.0.0.1
UMBRAL_SMTP_PORT=1025
UMBRAL_SMTP_TLS=0
UMBRAL_CORREO_REMITENTE=umbral@mazariegoscarlos.com
```

Los correos aparecen en <http://localhost:8025>.

---

## 6. Abrirlo desde el celular

Un celular no deja que una página revise sus puertos, así que en el celular
Umbral sirve para **leer** las revisiones de tus computadoras.

1. Conecta el celular al **mismo Wi-Fi** que la computadora donde corre Umbral.
2. Averigua la dirección de la computadora:
   - Kali: `hostname -I` (toma el primer número, por ejemplo `192.168.1.74`)
   - Windows: `ipconfig` y busca «Dirección IPv4»
3. En el navegador del celular escribe `http://192.168.1.74:8000` (con tu
   número).
4. Si no abre, el cortafuegos de la computadora está bloqueando el puerto 8000:
   - Windows: la primera vez que arranca Umbral aparece un aviso de «Firewall
     de Windows»; elige **Permitir**.
   - Kali con ufw: `sudo ufw allow 8000/tcp`

Para que el enlace del correo también funcione desde el celular, pon en
`backend/.env` la línea `UMBRAL_URL_SITIO=http://192.168.1.74:8000` y reinicia.

---

## 7. Correr las pruebas

El proyecto trae pruebas automáticas que recorren registro, confirmación,
bloqueo por intentos, agente, revisiones y aislamiento entre cuentas.

```bash
cd backend
.venv/bin/pip install -r requirements-dev.txt     # Windows: .venv\Scripts\pip
.venv/bin/python -m pytest -q                      # Windows: .venv\Scripts\python
```

**Qué deberías ver:** `10 passed`.

---

## 8. Publicarlo en internet

La guía completa, con capturas y clic por clic, viene en el PDF de despliegue.
En corto:

1. **Railway** (plan Hobby, 5 USD al mes): *New Project > Deploy from GitHub
   repo > umbral*. Railway lee el `Dockerfile` y `railway.toml` solo.
2. En el mismo proyecto: *Create > Database > PostgreSQL*.
3. En el servicio de Umbral, pestaña **Variables**, pega las de
   `.env.produccion.example` (con `DATABASE_URL=${{Postgres.DATABASE_URL}}`).
4. **Settings > Networking > Custom Domain**: `umbral.mazariegoscarlos.com`.
   Railway te da un registro CNAME y uno TXT; cópialos en el DNS de Porkbun.
5. **Resend**: agrega tu dominio, copia sus registros DNS a Porkbun y pega la
   llave en `UMBRAL_RESEND_API_KEY`.

¿Por qué Resend y no Gmail? Railway cierra el puerto SMTP en sus planes Free y
Hobby; los correos tienen que salir por una API web (HTTPS).

Si prefieres un servidor propio (VPS con Docker), sigue sirviendo:

```bash
DOMINIO=umbral.mazariegoscarlos.com docker compose up -d --build
```

---

## Si algo falla

| Lo que ves | Qué hacer |
|---|---|
| `python: command not found` (Windows) | Reinstala Python marcando «Add python.exe to PATH» y abre una terminal nueva |
| `No module named venv` (Kali) | `sudo apt install -y python3-venv` |
| `iniciar.ps1 cannot be loaded` | Corre antes `Set-ExecutionPolicy -Scope Process Bypass` |
| `address already in use` | Ya hay algo en el puerto 8000. Cierra la otra ventana de Umbral |
| «No hay conexión con Umbral» en la página | La ventana de la terminal se cerró. Vuelve a correr el script |
| «Demasiados intentos seguidos» | Es el límite de seguridad. Espera unos minutos |
| «Por seguridad, esta cuenta está en pausa» | Fallaste 5 veces la contraseña. Espera 15 minutos o usa «¿Olvidaste tu contraseña?» |
| El agente dice «No se pudo llegar a…» | Revisa que Umbral esté encendido y que la dirección de `--servidor` sea correcta |
| Quiero empezar de cero | Apaga Umbral y borra el archivo `backend/umbral.db` |
| Windows dice que el script «no está firmado» | Corre `Unblock-File .\umbral-agente.ps1` y vuelve a intentarlo |
| No veo «Admin» en el menú | Tu correo debe estar en `UMBRAL_ADMINS` (en `.env` o en las Variables de Railway) |
