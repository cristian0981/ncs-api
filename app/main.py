"""Punto de entrada de la API del Bot de Control de NC.

Arranque local:
    uvicorn app.main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.session import init_db

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Arranque: crea las tablas locales si no existen.
    logger.info("Iniciando %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    init_db()
    if not settings.origin_db_configured:
        logger.warning("BD de origen sin configurar: sincronización deshabilitada.")
    if not settings.graph_configured:
        logger.warning("Microsoft Graph sin configurar: verificación de correo deshabilitada.")
    yield
    logger.info("Apagando %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API de control y auditoría de No Conformidades (Celsia / ISES).",
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Sistema"], summary="Estado del servicio")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "origin_db": settings.origin_db_configured,
        "graph": settings.graph_configured,
    }
