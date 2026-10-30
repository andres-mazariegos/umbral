# Conexion a la base de datos con SQLAlchemy.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

# check_same_thread=False es necesario para SQLite con FastAPI.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Abre una sesion de base de datos por peticion y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
