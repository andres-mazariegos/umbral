# Rutas de autenticacion: registro, verificacion, login y perfil.
import random

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import MODO_DEV
from ..database import get_db
from ..emailer import enviar_codigo
from ..security import (
    hashear_password,
    verificar_password,
    crear_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _nuevo_codigo() -> str:
    """Genera un codigo de 6 digitos."""
    return f"{random.randint(0, 999999):06d}"


@router.post("/register", response_model=schemas.MensajeOut)
def registrar(datos: schemas.RegistroIn, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ese correo ya esta registrado")

    codigo = _nuevo_codigo()
    usuario = models.Usuario(
        nombre=datos.nombre,
        email=datos.email,
        hashed_password=hashear_password(datos.password),
        verificado=False,
        codigo=codigo,
    )
    db.add(usuario)
    db.commit()

    enviar_codigo(datos.email, codigo)

    respuesta = schemas.MensajeOut(mensaje="Cuenta creada. Te enviamos un codigo a tu correo.")
    if MODO_DEV:
        respuesta.codigo_dev = codigo  # para probar sin correo real
    return respuesta


@router.post("/verify", response_model=schemas.MensajeOut)
def verificar(datos: schemas.VerificarIn, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No encontramos esa cuenta")
    if usuario.verificado:
        return schemas.MensajeOut(mensaje="Tu cuenta ya estaba verificada.")
    if usuario.codigo != datos.codigo:
        raise HTTPException(status_code=400, detail="El codigo no es correcto")

    usuario.verificado = True
    usuario.codigo = None
    db.commit()
    return schemas.MensajeOut(mensaje="Correo verificado. Ya puedes iniciar sesion.")


@router.post("/resend", response_model=schemas.MensajeOut)
def reenviar(datos: schemas.ReenviarIn, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No encontramos esa cuenta")
    if usuario.verificado:
        return schemas.MensajeOut(mensaje="Tu cuenta ya estaba verificada.")

    usuario.codigo = _nuevo_codigo()
    db.commit()
    enviar_codigo(usuario.email, usuario.codigo)

    respuesta = schemas.MensajeOut(mensaje="Te reenviamos el codigo.")
    if MODO_DEV:
        respuesta.codigo_dev = usuario.codigo
    return respuesta


@router.post("/login", response_model=schemas.TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 usa el campo "username"; aqui ese campo es el correo.
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form.username).first()
    if not usuario or not verificar_password(form.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )
    if not usuario.verificado:
        raise HTTPException(status_code=403, detail="Primero confirma tu correo con el codigo")

    token = crear_token(usuario.id)
    return schemas.TokenOut(access_token=token)


@router.get("/me", response_model=schemas.UsuarioOut)
def mi_perfil(usuario: models.Usuario = Depends(get_current_user)):
    return usuario
