# Conexion a la base de datos y la sesion que usa cada peticion.
# SQLite en tu computadora, PostgreSQL en Railway: el codigo es el mismo.
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

_es_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if _es_sqlite else {},
                       pool_pre_ping=not _es_sqlite)

if _es_sqlite:
    @event.listens_for(engine, "connect")
    def _ajustes_sqlite(conexion, _):
        # Sin esto SQLite ignora las llaves foraneas y los borrados en cascada.
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
