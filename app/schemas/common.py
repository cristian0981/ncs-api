"""Esquemas comunes / reutilizables."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Mensaje(BaseModel):
    """Respuesta simple de estado."""

    detail: str


class CorridaInfo(BaseModel):
    """Resumen de una corrida del bot (bitácora)."""

    id: int
    tipo: str
    estado: str
    inicio: datetime
    fin: datetime | None = None
    nc_procesadas: int
    nc_nuevas: int
    nc_con_alerta: int
    detalle: str | None = None

    model_config = {"from_attributes": True}
