"""Lógica de negocio de Contratistas."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.contratista import Contratista, CorreoContratista
from app.repositories.contratista_repository import ContratistaRepository
from app.schemas.contratista import (
    ContratistaCreate,
    ContratistaUpdate,
    CorreoCreate,
)


class ContratistaError(Exception):
    """Error de negocio de contratistas (p.ej. nombre duplicado)."""


class ContratistaService:
    def __init__(self, db: Session) -> None:
        self.repo = ContratistaRepository(db)

    def get(self, contratista_id: int) -> Contratista | None:
        return self.repo.get(contratista_id)

    def list(self, *, solo_activos: bool = False) -> list[Contratista]:
        return self.repo.list(solo_activos=solo_activos)

    def crear(self, data: ContratistaCreate) -> Contratista:
        if self.repo.get_by_nombre(data.nombre):
            raise ContratistaError(f"Ya existe un contratista '{data.nombre}'.")
        contratista = Contratista(nombre=data.nombre, nit=data.nit, activo=data.activo)
        for c in data.correos:
            contratista.correos.append(
                CorreoContratista(
                    correo=str(c.correo),
                    nombre_contacto=c.nombre_contacto,
                    rol=c.rol,
                    activo=c.activo,
                )
            )
        self.repo.add(contratista)
        self.repo.commit()
        return self.repo.get(contratista.id)  # type: ignore[return-value]

    def actualizar(
        self, contratista_id: int, data: ContratistaUpdate
    ) -> Contratista | None:
        contratista = self.repo.get(contratista_id)
        if contratista is None:
            return None
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(contratista, campo, valor)
        self.repo.commit()
        return self.repo.get(contratista_id)

    def agregar_correo(
        self, contratista_id: int, data: CorreoCreate
    ) -> Contratista | None:
        contratista = self.repo.get(contratista_id)
        if contratista is None:
            return None
        self.repo.add_correo(
            CorreoContratista(
                contratista_id=contratista_id,
                correo=str(data.correo),
                nombre_contacto=data.nombre_contacto,
                rol=data.rol,
                activo=data.activo,
            )
        )
        self.repo.commit()
        return self.repo.get(contratista_id)

    def eliminar(self, contratista_id: int) -> bool:
        contratista = self.repo.get(contratista_id)
        if contratista is None:
            return False
        self.repo.delete(contratista)
        self.repo.commit()
        return True
