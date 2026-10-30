# Esquemas de entrada y salida de la API (Pydantic).
from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field


# ----- Usuarios / autenticacion -----
class RegistroIn(BaseModel):
    nombre: str
    email: EmailStr
    password: str = Field(min_length=6)


class VerificarIn(BaseModel):
    email: EmailStr
    codigo: str


class ReenviarIn(BaseModel):
    email: EmailStr


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    verificado: bool

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MensajeOut(BaseModel):
    mensaje: str
    # Solo se llena en modo desarrollo, para probar sin correo real.
    codigo_dev: str | None = None


# ----- Revisiones / hallazgos -----
class HallazgoOut(BaseModel):
    puerto: int
    protocolo: str
    servicio: str
    nivel: str
    titulo: str
    explicacion: str
    riesgo: str
    recomendacion: str

    model_config = {"from_attributes": True}


class ResumenNiveles(BaseModel):
    ok: int = 0
    revisar: int = 0
    importante: int = 0


class RevisionOut(BaseModel):
    id: int
    objetivo: str
    origen: str
    created_at: datetime
    resumen: ResumenNiveles
    total: int
    hallazgos: List[HallazgoOut] = []


class RevisionResumenOut(BaseModel):
    id: int
    objetivo: str
    origen: str
    created_at: datetime
    resumen: ResumenNiveles
    total: int
