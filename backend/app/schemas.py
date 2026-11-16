# Validacion de todo lo que entra a la API.
# Regla de la casa: nada se guarda sin pasar por aqui. Cada campo tiene
# longitud maxima y solo acepta los caracteres que tienen sentido para el.
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?: [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")
NOMBRE_EQUIPO = re.compile(r"^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+(?:[ _-][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+)*$")
CODIGO_6 = re.compile(r"^\d{6}$")
CODIGO_ENLACE = re.compile(r"^[A-Z2-9]{4}-?[A-Z2-9]{4}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,80}$")
DIRECCION_IP = re.compile(r"^[0-9A-Fa-f:.]{1,64}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

# Las que mas aparecen en filtraciones. Cumplir la forma no basta si la clave es de dominio publico.
CLAVES_COMUNES = {
    "password123", "contraseña123", "contrasena123", "qwerty12345", "1234567890", "123456789a",
    "abc1234567", "password1234", "iloveyou123", "admin12345", "bienvenido1", "bienvenido123",
    "mexico12345", "chiapas12345", "america12345", "qwertyuiop1", "1q2w3e4r5t", "1qaz2wsx3edc",
    "teamomucho1", "hola123456", "umbral12345", "passw0rd123", "zaq12wsxcde3",
}


class Base(BaseModel):
    # extra="forbid": si mandan un campo que no esperamos, se rechaza la peticion.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def validar_nombre(v: str) -> str:
    v = re.sub(r"\s+", " ", v)
    if not (2 <= len(v) <= 60):
        raise ValueError("El nombre debe tener entre 2 y 60 letras.")
    if not SOLO_LETRAS.match(v):
        raise ValueError("El nombre solo puede llevar letras y espacios (sin números ni símbolos).")
    return v


def validar_clave(clave: str, email: str = "", nombre: str = "") -> str:
    if not (10 <= len(clave) <= 128):
        raise ValueError("La contraseña debe tener entre 10 y 128 caracteres.")
    if _CONTROL.search(clave):
        raise ValueError("La contraseña tiene caracteres no permitidos.")
    if not (re.search(r"[a-zñ]", clave) and re.search(r"[A-ZÑ]", clave) and re.search(r"\d", clave)):
        raise ValueError("La contraseña necesita al menos una minúscula, una mayúscula y un número.")
    baja = clave.lower()
    if baja in CLAVES_COMUNES or len(set(baja)) < 5:
        raise ValueError("Esa contraseña es demasiado común o repetitiva. Elige otra.")
    partes = [email.split("@")[0].lower()] + [p.lower() for p in nombre.split()]
    if any(len(p) >= 4 and p in baja for p in partes):
        raise ValueError("La contraseña no debe contener tu nombre ni tu correo.")
    return clave


def _correo(v: str) -> str:
    v = v.strip().lower()
    if len(v) > 254:
        raise ValueError("Correo demasiado largo.")
    return v


# ---------- cuenta ----------

class RegistroIn(Base):
    nombre: str = Field(max_length=80)
    email: EmailStr
    clave: str = Field(max_length=128)
    acepta: bool

    _n = field_validator("nombre")(validar_nombre)
    _e = field_validator("email")(_correo)

    @model_validator(mode="after")
    def _revisar(self):
        if not self.acepta:
            raise ValueError("Necesitas aceptar el aviso de privacidad para crear la cuenta.")
        validar_clave(self.clave, self.email, self.nombre)
        return self


class ConfirmarIn(Base):
    email: Optional[EmailStr] = None
    codigo: Optional[str] = Field(default=None, max_length=6)
    pase: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def _revisar(self):
        if self.pase:
            if not TOKEN.match(self.pase):
                raise ValueError("El enlace no es válido.")
        elif not (self.email and self.codigo and CODIGO_6.match(self.codigo)):
            raise ValueError("Escribe los 6 números del código.")
        if self.email:
            self.email = _correo(self.email)
        return self


class CorreoIn(Base):
    email: EmailStr
    _e = field_validator("email")(_correo)


class EntrarIn(Base):
    email: EmailStr
    clave: str = Field(min_length=1, max_length=128)
    _e = field_validator("email")(_correo)


class RestablecerIn(Base):
    pase: str = Field(max_length=80)
    clave: str = Field(max_length=128)

    @field_validator("pase")
    @classmethod
    def _p(cls, v):
        if not TOKEN.match(v):
            raise ValueError("El enlace no es válido.")
        return v


class NombreIn(Base):
    nombre: str = Field(max_length=80)
    _n = field_validator("nombre")(validar_nombre)


class CambiarClaveIn(Base):
    actual: str = Field(min_length=1, max_length=128)
    nueva: str = Field(max_length=128)


class ClaveIn(Base):
    clave: str = Field(min_length=1, max_length=128)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    creado: datetime


# ---------- equipos y agente ----------

def validar_nombre_equipo(v: str) -> str:
    v = re.sub(r"\s+", " ", v)
    if not (2 <= len(v) <= 40) or not NOMBRE_EQUIPO.match(v):
        raise ValueError("El nombre del equipo lleva de 2 a 40 letras o números (puedes usar espacios, guion y guion bajo).")
    return v


class EnlaceIn(Base):
    nombre: str = Field(max_length=60)
    permiso: bool
    _n = field_validator("nombre")(validar_nombre_equipo)

    @field_validator("permiso")
    @classmethod
    def _p(cls, v):
        if not v:
            raise ValueError("Sin tu permiso no se puede conectar un equipo.")
        return v


class RenombrarIn(Base):
    nombre: str = Field(max_length=60)
    _n = field_validator("nombre")(validar_nombre_equipo)


class EnlazarIn(Base):
    codigo: str = Field(max_length=12)
    sistema: str = Field(default="", max_length=20, pattern=r"^[a-z0-9]{0,20}$")
    detalle_sistema: str = Field(default="", max_length=120)

    @field_validator("codigo")
    @classmethod
    def _c(cls, v):
        v = v.upper()
        if not CODIGO_ENLACE.match(v):
            raise ValueError("Ese código no tiene el formato correcto (ejemplo: K7QM-2XRD).")
        return v if "-" in v else f"{v[:4]}-{v[4:]}"

    @field_validator("detalle_sistema")
    @classmethod
    def _d(cls, v):
        return _CONTROL.sub("", v)


class PuertoIn(Base):
    puerto: int = Field(ge=1, le=65535)
    protocolo: Literal["tcp", "udp"] = "tcp"
    direccion: str = Field(default="0.0.0.0", max_length=64)
    proceso: str = Field(default="", max_length=80)
    ruta: str = Field(default="", max_length=260)

    @field_validator("direccion")
    @classmethod
    def _dir(cls, v):
        if not DIRECCION_IP.match(v):
            raise ValueError("Dirección inválida.")
        return v

    @field_validator("proceso", "ruta")
    @classmethod
    def _limpiar(cls, v):
        return _CONTROL.sub("", v)


class ReporteIn(BaseModel):
    # Aqui se ignoran campos extra a proposito: asi un agente mas nuevo sigue funcionando.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    sistema: str = Field(default="", max_length=20, pattern=r"^[a-z0-9]{0,20}$")
    detalle_sistema: str = Field(default="", max_length=120)
    cortafuegos: Literal["activo", "apagado", "desconocido"] = "desconocido"
    puertos: list[PuertoIn] = Field(max_length=400)

    @field_validator("detalle_sistema")
    @classmethod
    def _d(cls, v):
        return _CONTROL.sub("", v)


class EstadoIn(Base):
    estado: Literal["pendiente", "resuelto", "aceptado"]
