"""Dependencias compartidas de la API (inyección de servicios)."""
from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auditoria_service import AuditoriaService
from app.services.contratista_service import ContratistaService
from app.services.nc_service import NCService
from app.services.supervisor_service import SupervisorService


def get_nc_service(db: Session = Depends(get_db)) -> NCService:
    return NCService(db)


def get_contratista_service(db: Session = Depends(get_db)) -> ContratistaService:
    return ContratistaService(db)


def get_supervisor_service(db: Session = Depends(get_db)) -> SupervisorService:
    return SupervisorService(db)


def get_auditoria_service(db: Session = Depends(get_db)) -> AuditoriaService:
    return AuditoriaService(db)


# Re-exportado por comodidad.
__all__ = [
    "get_db",
    "get_nc_service",
    "get_contratista_service",
    "get_supervisor_service",
    "get_auditoria_service",
    "Generator",
]
