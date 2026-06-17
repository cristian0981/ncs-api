"""Endpoints de auditoría: ejecutar el bot y consultar la bitácora.

La auditoría corre en segundo plano (BackgroundTasks) con su propia sesión de
BD, porque la sesión de la petición se cierra al responder.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories.bitacora_repository import BitacoraRepository
from app.schemas.common import CorridaInfo, Mensaje
from app.services.auditoria_service import AuditoriaService

logger = get_logger(__name__)

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


def _correr_auditoria() -> None:
    """Tarea de fondo: abre su propia sesión, audita y la cierra."""
    db = SessionLocal()
    try:
        registro = AuditoriaService(db).ejecutar()
        logger.info("Auditoría finalizada: %s", registro.detalle)
    finally:
        db.close()


@router.post("/ejecutar", response_model=Mensaje, summary="Ejecutar auditoría ahora")
def ejecutar(background_tasks: BackgroundTasks) -> Mensaje:
    background_tasks.add_task(_correr_auditoria)
    return Mensaje(detail="Auditoría iniciada en segundo plano.")


@router.get("/ultima", response_model=CorridaInfo | None, summary="Última corrida")
def ultima(db: Session = Depends(get_db)) -> CorridaInfo | None:
    registro = BitacoraRepository(db).ultima()
    return registro


@router.get("/bitacora", response_model=list[CorridaInfo], summary="Historial de corridas")
def bitacora(limit: int = 20, db: Session = Depends(get_db)) -> list[CorridaInfo]:
    return BitacoraRepository(db).listar(limit=limit)
