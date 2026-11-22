# Umbral

Tu computadora tiene 65,535 puertas (puertos). Umbral revisa cuáles están
abiertas, con tu permiso, y te explica cada una en lenguaje sencillo: qué es,
qué puede pasar y cómo cerrarla en Windows o en Linux.

La idea de fondo: la seguridad informática no debería ser solo para «los que
saben». Cualquier persona con una computadora merece entender qué pasa en ella.

Proyecto de la materia Seguridad Informática (7.º cuatrimestre), Universidad
Politécnica de Chiapas. Por Carlos Andrés Mazariegos Laguna (243790).

## Qué hace

- Cuenta con registro, confirmación por correo, inicio de sesión y recuperación de contraseña.
- Un agente que corre en tu equipo, pide permiso en pantalla y lee los puertos abiertos: en Linux (Kali, Ubuntu) es un archivo de Python y en Windows uno de PowerShell, así que no hay que instalar nada.
- Cada puerto se traduce a tres niveles: **Tranquilo**, **Ojo aquí** y **Atiéndelo ya**, con pasos para cerrarlo.
- Detecta señales de alarma: puertos típicos de herramientas de ataque, programas que corren desde carpetas temporales y programas de control remoto.
- Compara cada revisión con la anterior y avisa qué puerta se abrió o se cerró.
- Se adapta al celular para leer las revisiones desde cualquier lado.
- Rol de administrador: cifras generales, cuentas (con correos tapados), desbloqueo de cuentas y bitácora de seguridad del sitio.

## Arrancarlo

Necesitas [Python 3.11+](https://www.python.org/downloads/) y [Node.js 20+](https://nodejs.org/).

| Sistema | Comando (dentro de la carpeta del proyecto) |
|---|---|
| Linux / Kali | `./iniciar.sh` |
| Windows (PowerShell) | `.\iniciar.ps1` |

Después abre <http://localhost:8000>. La guía completa, paso a paso, está en
[docs/GUIA.md](docs/GUIA.md).

## Cómo está armado

```
umbral/
├── backend/      API en FastAPI (cuenta, equipos, revisiones, intérprete, administración)
│   ├── app/
│   └── tests/    pruebas de punta a punta (python -m pytest)
├── agent/        umbral_agente.py (Linux) y umbral-agente.ps1 (Windows)
├── reglas/       regla propia de Semgrep (CWE-939)
├── frontend/     sitio en React + Vite
└── docs/         guía de instalación y medidas de seguridad
```

| Parte | Tecnología |
|---|---|
| Sitio | React 19, React Router, Vite, CSS propio |
| API | Python, FastAPI, SQLAlchemy, Pydantic |
| Base de datos | SQLite en tu equipo, PostgreSQL en Railway |
| Seguridad | Argon2id, JWT en cookie HttpOnly, códigos de un solo uso, límite de intentos |
| Análisis | psutil; si no está, `ss` (Linux). En Windows, `Get-NetTCPConnection` |
| Correo | Resend (API por HTTPS) o SMTP |
| Publicación | Docker en Railway (o Docker + Caddy en un servidor propio) |
| Análisis de código | CodeQL (GitHub) y Semgrep |

Las medidas de seguridad, una por una y dónde está cada una en el código:
[docs/SEGURIDAD.md](docs/SEGURIDAD.md).

## Uso responsable

Conecta solo equipos tuyos o sobre los que tengas autorización. El agente
únicamente lee los puertos del equipo donde lo ejecutas; no escanea otros
equipos de la red.
