<p align="center"><img src="logo.png" width="120" alt="Umbral"></p>

![Vista previa de Umbral](preview.png)

# Umbral

Tu computadora tiene 65,535 puertas (puertos). Umbral revisa cuÃ¡les estÃ¡n
abiertas, con tu permiso, y te explica cada una en lenguaje sencillo: quÃ© es,
quÃ© puede pasar y cÃ³mo cerrarla en Windows o en Linux.

La idea de fondo: la seguridad informÃ¡tica no deberÃ­a ser solo para Â«los que
sabenÂ». Cualquier persona con una computadora merece entender quÃ© pasa en ella.

Proyecto de la materia Seguridad InformÃ¡tica (7.Âº cuatrimestre), Universidad
PolitÃ©cnica de Chiapas. Por Carlos AndrÃ©s Mazariegos Laguna (243790).

## QuÃ© hace

- Cuenta con registro, confirmaciÃ³n por correo, inicio de sesiÃ³n y recuperaciÃ³n de contraseÃ±a.
- Un agente que corre en tu equipo, pide permiso en pantalla y lee los puertos abiertos: en Linux (Kali, Ubuntu) es un archivo de Python y en Windows uno de PowerShell, asÃ­ que no hay que instalar nada.
- Cada puerto se traduce a tres niveles: **Tranquilo**, **Ojo aquÃ­** y **AtiÃ©ndelo ya**, con pasos para cerrarlo.
- Detecta seÃ±ales de alarma: puertos tÃ­picos de herramientas de ataque, programas que corren desde carpetas temporales y programas de control remoto.
- Compara cada revisiÃ³n con la anterior y avisa quÃ© puerta se abriÃ³ o se cerrÃ³.
- Se adapta al celular para leer las revisiones desde cualquier lado.
- Rol de administrador: cifras generales, cuentas (con correos tapados), desbloqueo de cuentas y bitÃ¡cora de seguridad del sitio.

## Arrancarlo

Necesitas [Python 3.11+](https://www.python.org/downloads/) y [Node.js 20+](https://nodejs.org/).

| Sistema | Comando (dentro de la carpeta del proyecto) |
|---|---|
| Linux / Kali | `./iniciar.sh` |
| Windows (PowerShell) | `.\iniciar.ps1` |

DespuÃ©s abre <http://localhost:8000>. La guÃ­a completa, paso a paso, estÃ¡ en
[docs/GUIA.md](docs/GUIA.md).

## CÃ³mo estÃ¡ armado

```
umbral/
â”œâ”€â”€ backend/      API en FastAPI (cuenta, equipos, revisiones, intÃ©rprete, administraciÃ³n)
â”‚   â”œâ”€â”€ app/
â”‚   â””â”€â”€ tests/    pruebas de punta a punta (python -m pytest)
â”œâ”€â”€ agent/        umbral_agente.py (Linux) y umbral-agente.ps1 (Windows)
â”œâ”€â”€ reglas/       regla propia de Semgrep (CWE-939)
â”œâ”€â”€ frontend/     sitio en React + Vite
â””â”€â”€ docs/         guÃ­a de instalaciÃ³n y medidas de seguridad
```

| Parte | TecnologÃ­a |
|---|---|
| Sitio | React 19, React Router, Vite, CSS propio |
| API | Python, FastAPI, SQLAlchemy, Pydantic |
| Base de datos | SQLite en tu equipo, PostgreSQL en Railway |
| Seguridad | Argon2id, JWT en cookie HttpOnly, cÃ³digos de un solo uso, lÃ­mite de intentos |
| AnÃ¡lisis | psutil; si no estÃ¡, `ss` (Linux). En Windows, `Get-NetTCPConnection` |
| Correo | Resend (API por HTTPS) o SMTP |
| PublicaciÃ³n | Docker en Railway (o Docker + Caddy en un servidor propio) |
| AnÃ¡lisis de cÃ³digo | CodeQL (GitHub) y Semgrep |

Las medidas de seguridad, una por una y dÃ³nde estÃ¡ cada una en el cÃ³digo:
[docs/SEGURIDAD.md](docs/SEGURIDAD.md).

## Uso responsable

Conecta solo equipos tuyos o sobre los que tengas autorizaciÃ³n. El agente
Ãºnicamente lee los puertos del equipo donde lo ejecutas; no escanea otros
equipos de la red.
