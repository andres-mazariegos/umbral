# Tablas de la base de datos: usuarios, revisiones y hallazgos.
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    verificado = Column(Boolean, default=False)
    codigo = Column(String, nullable=True)  # codigo de verificacion
    created_at = Column(DateTime, default=datetime.utcnow)

    revisiones = relationship("Revision", back_populates="usuario", cascade="all, delete-orphan")


class Revision(Base):
    __tablename__ = "revisiones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    objetivo = Column(String, default="127.0.0.1")
    origen = Column(String, default="psutil")  # psutil / nmap / simulado
    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="revisiones")
    hallazgos = relationship("Hallazgo", back_populates="revision", cascade="all, delete-orphan")


class Hallazgo(Base):
    __tablename__ = "hallazgos"

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revisiones.id"), nullable=False)
    puerto = Column(Integer, nullable=False)
    protocolo = Column(String, default="tcp")
    servicio = Column(String, default="")
    nivel = Column(String, default="revisar")  # ok / revisar / importante
    titulo = Column(String, default="")
    explicacion = Column(Text, default="")
    riesgo = Column(Text, default="")
    recomendacion = Column(Text, default="")

    revision = relationship("Revision", back_populates="hallazgos")
