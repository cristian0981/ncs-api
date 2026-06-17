"""Esquemas de Contratista y sus correos."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


# --- Correos ---
class CorreoBase(BaseModel):
    correo: EmailStr
    nombre_contacto: str | None = None
    rol: str | None = None
    activo: bool = True


class CorreoCreate(CorreoBase):
    pass


class CorreoRead(CorreoBase):
    id: int
    model_config = {"from_attributes": True}


# --- Contratista ---
class ContratistaBase(BaseModel):
    nombre: str
    nit: str | None = None
    activo: bool = True


class ContratistaCreate(ContratistaBase):
    correos: list[CorreoCreate] = []


class ContratistaUpdate(BaseModel):
    nombre: str | None = None
    nit: str | None = None
    activo: bool | None = None


class ContratistaRead(ContratistaBase):
    id: int
    correos: list[CorreoRead] = []
    model_config = {"from_attributes": True}
