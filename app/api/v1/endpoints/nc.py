"""Endpoints de No Conformidades: estadisticas, alertas, filtros y detalle."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_nc_service
from app.schemas.nc import FiltrosDisponibles, NCAlerta, NCRead, NCStats
from app.services.nc_service import NCService

router = APIRouter(prefix="/nc", tags=["No Conformidades"])


@router.get("/stats", response_model=NCStats, summary="Tarjetas del dashboard")
def stats(service: NCService = Depends(get_nc_service)) -> NCStats:
    return service.get_stats()


@router.get("/alertas", response_model=list[NCAlerta], summary="NCs criticas / por vencer")
def alertas(service: NCService = Depends(get_nc_service)) -> list[NCAlerta]:
    return service.get_alertas()


@router.get("/filtros", response_model=FiltrosDisponibles, summary="Valores de filtro disponibles")
def filtros(service: NCService = Depends(get_nc_service)) -> FiltrosDisponibles:
    return service.get_filtros()


@router.get("", response_model=list[NCRead], summary="Listar NCs con filtros")
def listar(
    supervisor_id: int | None = Query(default=None, description="Acota a las zonas del supervisor"),
    zona: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    tipo_actividad: str | None = Query(default=None),
    estado_notificacion: str | None = Query(default=None),
    semaforo: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: NCService = Depends(get_nc_service),
) -> list[NCRead]:
    return service.list(
        supervisor_id=supervisor_id,
        zona=zona,
        sector=sector,
        tipo_actividad=tipo_actividad,
        estado_notificacion=estado_notificacion,
        semaforo=semaforo,
        skip=skip,
        limit=limit,
    )


@router.get("/{nc_id}", response_model=NCRead, summary="Detalle de una NC")
def detalle(nc_id: int, service: NCService = Depends(get_nc_service)) -> NCRead:
    nc = service.get(nc_id)
    if nc is None:
        raise HTTPException(status_code=404, detail="NC no encontrada")
    return nc
