"""Endpoints de administracion de Supervisores y sus zonas."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_supervisor_service
from app.schemas.common import Mensaje
from app.schemas.supervisor import (
    SupervisorCreate,
    SupervisorRead,
    SupervisorUpdate,
    ZonaAsignar,
)
from app.services.supervisor_service import SupervisorService

router = APIRouter(prefix="/supervisores", tags=["Supervisores"])


@router.get("", response_model=list[SupervisorRead], summary="Listar supervisores")
def listar(
    solo_activos: bool = False,
    service: SupervisorService = Depends(get_supervisor_service),
) -> list[SupervisorRead]:
    return service.list(solo_activos=solo_activos)


@router.get("/{supervisor_id}", response_model=SupervisorRead)
def obtener(
    supervisor_id: int,
    service: SupervisorService = Depends(get_supervisor_service),
) -> SupervisorRead:
    sup = service.get(supervisor_id)
    if sup is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return sup


@router.post("", response_model=SupervisorRead, status_code=status.HTTP_201_CREATED)
def crear(
    data: SupervisorCreate,
    service: SupervisorService = Depends(get_supervisor_service),
) -> SupervisorRead:
    return service.crear(data)


@router.put("/{supervisor_id}", response_model=SupervisorRead)
def actualizar(
    supervisor_id: int,
    data: SupervisorUpdate,
    service: SupervisorService = Depends(get_supervisor_service),
) -> SupervisorRead:
    sup = service.actualizar(supervisor_id, data)
    if sup is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return sup


@router.post("/{supervisor_id}/zonas", response_model=SupervisorRead, summary="Asignar zona")
def asignar_zona(
    supervisor_id: int,
    data: ZonaAsignar,
    service: SupervisorService = Depends(get_supervisor_service),
) -> SupervisorRead:
    sup = service.asignar_zona(supervisor_id, data.zona)
    if sup is None:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return sup


@router.delete("/{supervisor_id}", response_model=Mensaje)
def eliminar(
    supervisor_id: int,
    service: SupervisorService = Depends(get_supervisor_service),
) -> Mensaje:
    if not service.eliminar(supervisor_id):
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    return Mensaje(detail="Supervisor eliminado")
