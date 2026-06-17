"""Endpoints de administración de Contratistas y sus correos."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_contratista_service
from app.schemas.common import Mensaje
from app.schemas.contratista import (
    ContratistaCreate,
    ContratistaRead,
    ContratistaUpdate,
    CorreoCreate,
)
from app.services.contratista_service import ContratistaError, ContratistaService

router = APIRouter(prefix="/contratistas", tags=["Contratistas"])


@router.get("", response_model=list[ContratistaRead], summary="Listar contratistas")
def listar(
    solo_activos: bool = False,
    service: ContratistaService = Depends(get_contratista_service),
) -> list[ContratistaRead]:
    return service.list(solo_activos=solo_activos)


@router.get("/{contratista_id}", response_model=ContratistaRead)
def obtener(
    contratista_id: int,
    service: ContratistaService = Depends(get_contratista_service),
) -> ContratistaRead:
    contratista = service.get(contratista_id)
    if contratista is None:
        raise HTTPException(status_code=404, detail="Contratista no encontrado")
    return contratista


@router.post("", response_model=ContratistaRead, status_code=status.HTTP_201_CREATED)
def crear(
    data: ContratistaCreate,
    service: ContratistaService = Depends(get_contratista_service),
) -> ContratistaRead:
    try:
        return service.crear(data)
    except ContratistaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{contratista_id}", response_model=ContratistaRead)
def actualizar(
    contratista_id: int,
    data: ContratistaUpdate,
    service: ContratistaService = Depends(get_contratista_service),
) -> ContratistaRead:
    contratista = service.actualizar(contratista_id, data)
    if contratista is None:
        raise HTTPException(status_code=404, detail="Contratista no encontrado")
    return contratista


@router.post("/{contratista_id}/correos", response_model=ContratistaRead)
def agregar_correo(
    contratista_id: int,
    data: CorreoCreate,
    service: ContratistaService = Depends(get_contratista_service),
) -> ContratistaRead:
    contratista = service.agregar_correo(contratista_id, data)
    if contratista is None:
        raise HTTPException(status_code=404, detail="Contratista no encontrado")
    return contratista


@router.delete("/{contratista_id}", response_model=Mensaje)
def eliminar(
    contratista_id: int,
    service: ContratistaService = Depends(get_contratista_service),
) -> Mensaje:
    if not service.eliminar(contratista_id):
        raise HTTPException(status_code=404, detail="Contratista no encontrado")
    return Mensaje(detail="Contratista eliminado")
