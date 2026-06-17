"""Esquemas de Supervisor y sus zonas."""
from __future__ import annotations

from pydantic import BaseModel


class SupervisorBase(BaseModel):
    nombre: str
    correo: str | None = None
    activo: bool = True


class SupervisorCreate(SupervisorBase):
    zonas: list[str] = []


class SupervisorUpdate(BaseModel):
    nombre: str | None = None
    correo: str | None = None
    activo: bool | None = None


class ZonaAsignar(BaseModel):
    zona: str


class SupervisorRead(SupervisorBase):
    id: int
    zonas: list[str] = []

    model_config = {"from_attributes": True}
