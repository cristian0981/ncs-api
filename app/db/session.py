"""Conexión a la base de datos LOCAL de control.

Aquí vive el estado del bot (NCs en control, contratistas, bitácora). Por
defecto es SQLite, pero `LOCAL_DATABASE_URL` permite migrar a otro motor sin
cambiar código.
"""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite necesita check_same_thread=False para usarse con FastAPI.
_connect_args = (
    {"check_same_thread": False}
    if settings.LOCAL_DATABASE_URL.startswith("sqlite")
    else {}
)

# Asegura que la carpeta del archivo SQLite exista.
if settings.LOCAL_DATABASE_URL.startswith("sqlite:///"):
    _db_path = settings.LOCAL_DATABASE_URL.replace("sqlite:///", "", 1)
    _dir = os.path.dirname(_db_path)
    if _dir:
        os.makedirs(_dir, exist_ok=True)

engine = create_engine(
    settings.LOCAL_DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas locales si no existen. Se llama al arrancar la app."""
    # Importa los modelos para registrarlos en Base.metadata.
    from app.db.base import Base
    import app.models  # noqa: F401  (registra todos los modelos)

    Base.metadata.create_all(bind=engine)
