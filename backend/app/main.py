# Punto de entrada de la API de Umbral (FastAPI).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ORIGENES_CORS
from .database import Base, engine
from . import models  # noqa: F401  (necesario para que se creen las tablas)
from .routers import auth, scans

# Crea las tablas la primera vez que arranca.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Umbral API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scans.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Umbral"}
