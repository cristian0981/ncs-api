"""Conexión de SOLO LECTURA a la base de datos de ORIGEN (Formap).

De aquí se extraen las actividades calificadas como NC. El engine se crea de
forma perezosa (lazy) y solo si `ORIGIN_DATABASE_URL` está configurada, para
que la app pueda arrancar y desarrollarse aunque todavía no haya credenciales.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionOrigin: sessionmaker | None = None


def get_origin_engine() -> Engine | None:
    """Devuelve (creando si hace falta) el engine de la BD de origen.

    Retorna None si todavía no se ha configurado la conexión.
    """
    global _engine, _SessionOrigin

    if not settings.origin_db_configured:
        logger.warning("ORIGIN_DATABASE_URL no configurada: la sincronización está deshabilitada.")
        return None

    if _engine is None:
        # BD de origen = SQL Server (Formap). Se usa SOLO para lectura;
        # la app nunca emite escrituras por esta conexion.
        _engine = create_engine(
            settings.ORIGIN_DATABASE_URL,
            pool_pre_ping=True,
            future=True,
        )
        _SessionOrigin = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
        logger.info("Engine de BD de origen inicializado.")

    return _engine


def get_origin_db() -> Generator[Session | None, None, None]:
    """Dependencia opcional: sesión de la BD de origen o None si no hay conexión."""
    if get_origin_engine() is None or _SessionOrigin is None:
        yield None
        return
    db = _SessionOrigin()
    try:
        yield db
    finally:
        db.close()
