# Tablas de Umbral.
#   usuarios   -> la cuenta
#   pases      -> codigos y enlaces de un solo uso (confirmar correo, cambiar contraseña)
#   equipos    -> computadoras conectadas con el agente
#   enlaces    -> codigo temporal para conectar un equipo nuevo
#   revisiones -> cada vez que se revisa un equipo
#   hallazgos  -> cada puerta (puerto) encontrada en una revision
#   eventos    -> bitacora de seguridad (quien entro, desde donde, que fallo)
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from .database import Base


def ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(60), nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    hash_clave = Column(String(255), nullable=False)
    verificado = Column(Boolean, default=False, nullable=False)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime, nullable=True)
    # Sube de numero al cambiar la contraseña: todas las sesiones viejas dejan de servir.
    version_sesion = Column(Integer, default=1, nullable=False)
    creado = Column(DateTime, default=ahora, nullable=False)
    ultimo_acceso = Column(DateTime, nullable=True)

    pases = relationship("Pase", cascade="all, delete-orphan", back_populates="usuario")
    equipos = relationship("Equipo", cascade="all, delete-orphan", back_populates="usuario")
    enlaces = relationship("Enlace", cascade="all, delete-orphan")
    revisiones = relationship("Revision", cascade="all, delete-orphan", back_populates="usuario")
    eventos = relationship("Evento", cascade="all, delete-orphan")


class Pase(Base):
    __tablename__ = "pases"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)          # confirmar / restablecer
    hash_token = Column(String(64), nullable=False, index=True)   # enlace del correo
    hash_codigo = Column(String(64), nullable=True)               # codigo de 6 digitos
    expira = Column(DateTime, nullable=False)
    intentos = Column(Integer, default=0, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    creado = Column(DateTime, default=ahora, nullable=False)

    usuario = relationship("Usuario", back_populates="pases")


class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(40), nullable=False)
    sistema = Column(String(20), default="", nullable=False)       # windows / linux / mac
    detalle_sistema = Column(String(120), default="", nullable=False)
    hash_llave = Column(String(64), nullable=False, unique=True)   # credencial del agente
    activo = Column(Boolean, default=True, nullable=False)
    creado = Column(DateTime, default=ahora, nullable=False)
    ultima_senal = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", back_populates="equipos")
    revisiones = relationship("Revision", back_populates="equipo")


class Enlace(Base):
    __tablename__ = "enlaces"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    hash_codigo = Column(String(64), nullable=False, unique=True)
    nombre_equipo = Column(String(40), nullable=False)
    expira = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    equipo_id = Column(Integer, nullable=True)
    creado = Column(DateTime, default=ahora, nullable=False)


class Revision(Base):
    __tablename__ = "revisiones"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre_equipo = Column(String(40), default="", nullable=False)
    origen = Column(String(12), default="agente", nullable=False)   # agente / directa / ejemplo
    sistema = Column(String(20), default="", nullable=False)
    cortafuegos = Column(String(16), default="desconocido", nullable=False)  # activo / apagado / desconocido
    creado = Column(DateTime, default=ahora, nullable=False)

    usuario = relationship("Usuario", back_populates="revisiones")
    equipo = relationship("Equipo", back_populates="revisiones")
    hallazgos = relationship("Hallazgo", cascade="all, delete-orphan", back_populates="revision",
                             order_by="Hallazgo.orden")


class Hallazgo(Base):
    __tablename__ = "hallazgos"

    id = Column(Integer, primary_key=True)
    revision_id = Column(Integer, ForeignKey("revisiones.id", ondelete="CASCADE"), nullable=False, index=True)
    orden = Column(Integer, default=0, nullable=False)
    puerto = Column(Integer, nullable=False)
    protocolo = Column(String(4), default="tcp", nullable=False)
    direccion = Column(String(64), default="", nullable=False)
    alcance = Column(String(8), default="red", nullable=False)     # red / interno
    proceso = Column(String(80), default="", nullable=False)
    ruta = Column(String(260), default="", nullable=False)
    servicio = Column(String(60), default="", nullable=False)
    nivel = Column(String(10), default="atento", nullable=False)   # tranquilo / atento / urgente
    titulo = Column(String(140), default="", nullable=False)
    explicacion = Column(Text, default="", nullable=False)
    riesgo = Column(Text, default="", nullable=False)
    pasos = Column(Text, default="{}", nullable=False)             # JSON {"windows": [...], "linux": [...]}
    senales = Column(Text, default="[]", nullable=False)           # JSON con avisos extra
    estado = Column(String(12), default="pendiente", nullable=False)  # pendiente / resuelto / aceptado

    revision = relationship("Revision", back_populates="hallazgos")


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True, index=True)
    tipo = Column(String(40), nullable=False)
    ip = Column(String(64), default="", nullable=False)
    detalle = Column(String(200), default="", nullable=False)
    creado = Column(DateTime, default=ahora, nullable=False)


Index("ix_revisiones_usuario_fecha", Revision.usuario_id, Revision.creado)
