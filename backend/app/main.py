# Punto de entrada de la API de Umbral (FastAPI).
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as HTTPExceptionBase

from . import config, models  # noqa: F401  (models: necesario para crear las tablas)
from .database import Base, engine
from .routers import admin, auth, cuenta, equipos, revisiones

Base.metadata.create_all(bind=engine)

# En produccion no se publica la documentacion automatica de la API.
app = FastAPI(title="Umbral API", version="2.0.0",
              docs_url="/api/docs" if config.MODO_DEV else None, redoc_url=None,
              openapi_url="/api/openapi.json" if config.MODO_DEV else None)

app.add_middleware(CORSMiddleware, allow_origins=config.ORIGENES_CORS, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type", "X-Umbral"])

CABECERAS = {
    "X-Content-Type-Options": "nosniff",                  # el navegador no adivina tipos de archivo
    "X-Frame-Options": "DENY",                            # nadie puede meter Umbral en un marco (clickjacking)
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                               "script-src 'self'; font-src 'self' data:; connect-src 'self'; object-src 'none'; "
                               "base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
}
TAMANO_MAXIMO = 256 * 1024      # 256 KB: ninguna peticion legitima de Umbral pesa mas


@app.middleware("http")
async def escudo(request: Request, call_next):
    ruta, metodo = request.url.path, request.method

    largo = request.headers.get("content-length")
    if largo and (not largo.isdigit() or int(largo) > TAMANO_MAXIMO):
        return JSONResponse({"detail": "La petición es demasiado grande."}, status_code=413)

    # Defensa contra CSRF: toda accion del sitio debe traer la cabecera X-Umbral,
    # que un formulario de otro sitio no puede poner. El agente no usa cookies, usa su llave.
    if metodo not in ("GET", "HEAD", "OPTIONS") and ruta.startswith("/api/") and not ruta.startswith("/api/agente/"):
        if request.headers.get("x-umbral") != "web":
            return JSONResponse({"detail": "Petición no permitida."}, status_code=403)
        origen = request.headers.get("origin")
        if origen and origen not in config.ORIGENES_CORS and origen.split("//")[-1] != request.headers.get("host"):
            return JSONResponse({"detail": "Origen no permitido."}, status_code=403)

    respuesta = await call_next(request)
    for nombre, valor in CABECERAS.items():
        respuesta.headers.setdefault(nombre, valor)
    if not config.MODO_DEV:
        respuesta.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if ruta.startswith("/api/"):
        respuesta.headers["Cache-Control"] = "no-store"     # nada de la cuenta se queda guardado en cache
    return respuesta


@app.exception_handler(RequestValidationError)
async def datos_invalidos(request: Request, exc: RequestValidationError):
    """Convierte los errores de validacion en un mensaje claro por campo."""
    campos, primero = {}, ""
    for e in exc.errors():
        campo = str(e["loc"][-1]) if len(e["loc"]) > 1 else "general"
        mensaje = e["msg"].replace("Value error, ", "")
        if e["type"] != "value_error":
            mensaje = {"missing": "Este dato es obligatorio.", "extra_forbidden": "Dato no permitido.",
                       "string_too_long": "Es demasiado largo."}.get(e["type"], "El dato no es válido.")
            if campo == "email":
                mensaje = "Escribe un correo válido, como nombre@dominio.com."
        campos.setdefault(campo, mensaje)
        primero = primero or mensaje
    return JSONResponse({"detail": primero or "Revisa los datos.", "campos": campos}, status_code=422)


app.include_router(auth.router)
app.include_router(cuenta.router)
app.include_router(equipos.router)
app.include_router(revisiones.router)
app.include_router(admin.router)


@app.get("/api/salud")
def salud():
    return {"estado": "ok", "app": "Umbral"}


# Si existe la carpeta frontend/dist (npm run build), la API tambien sirve el sitio:
# asi todo vive en una sola direccion y la cookie de sesion no cruza dominios.
if config.RUTA_WEB.exists():
    app.mount("/assets", StaticFiles(directory=config.RUTA_WEB / "assets"), name="assets")

    @app.exception_handler(HTTPExceptionBase)
    async def sitio(request: Request, exc: HTTPExceptionBase):
        if exc.status_code == 404 and not request.url.path.startswith("/api/") and request.method == "GET":
            archivo = (config.RUTA_WEB / request.url.path.lstrip("/")).resolve()
            if archivo.is_file() and config.RUTA_WEB.resolve() in archivo.parents:
                return FileResponse(archivo)
            return FileResponse(config.RUTA_WEB / "index.html")
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None))
