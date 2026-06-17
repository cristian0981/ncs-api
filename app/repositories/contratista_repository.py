"""Acceso a datos de Contratistas y sus correos."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.contratista import Contratista, CorreoContratista


class ContratistaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, contratista_id: int) -> Contratista | None:
        stmt = (
            select(Contratista)
            .where(Contratista.id == contratista_id)
            .options(selectinload(Contratista.correos))
        )
        return self.db.scalars(stmt).first()

    def get_by_nombre(self, nombre: str) -> Contratista | None:
        stmt = select(Contratista).where(Contratista.nombre == nombre)
        return self.db.scalars(stmt).first()

    def list(self, *, solo_activos: bool = False) -> list[Contratista]:
        stmt = select(Contratista).options(selectinload(Contratista.correos))
        if solo_activos:
            stmt = stmt.where(Contratista.activo.is_(True))
        stmt = stmt.order_by(Contratista.nombre)
        return list(self.db.scalars(stmt).all())

    def add(self, contratista: Contratista) -> Contratista:
        self.db.add(contratista)
        self.db.flush()
        return contratista

    def add_correo(self, correo: CorreoContratista) -> CorreoContratista:
        self.db.add(correo)
        self.db.flush()
        return correo

    def delete(self, contratista: Contratista) -> None:
        self.db.delete(contratista)

    def commit(self) -> None:
        self.db.commit()
