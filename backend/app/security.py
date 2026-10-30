# Seguridad: hash de contraseñas y tokens JWT.
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .config import SECRET_KEY, ALGORITMO, HORAS_TOKEN
from .database import get_db

# Uso pbkdf2_sha256: viene con passlib y no necesita instalar nada extra.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# El frontend manda el token; esto le dice a FastAPI de donde sacarlo.
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def crear_token(usuario_id: int) -> str:
    expira = datetime.utcnow() + timedelta(hours=HORAS_TOKEN)
    datos = {"sub": str(usuario_id), "exp": expira}
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> models.Usuario:
    """Saca al usuario a partir del token. Si algo falla, devuelve 401."""
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No pudimos validar tu sesion",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        datos = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        usuario_id = int(datos.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise credenciales_invalidas

    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if usuario is None:
        raise credenciales_invalidas
    return usuario
