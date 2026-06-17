"""Acceso a datos de Supervisores y sus zonas."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.supervisor import Supervisor, SupervisorZona


class SupervisorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, supervisor_id: int) -> Supervisor | None:
        stmt = (
            select(Supervisor)
            .where(Supervisor.id == supervisor_id)
            .options(selectinload(Supervisor.zonas))
        )
        return self.db.scalars(stmt).first()

    def list(self, *, solo_activos: bool = False) -> list[Supervisor]:
        stmt = select(Supervisor).options(selectinload(Supervisor.zonas))
        if solo_activos:
            stmt = stmt.where(Supervisor.activo.is_(True))
        return list(self.db.scalars(stmt.order_by(Supervisor.nombre)).all())

    def zonas_de(self, supervisor_id: int) -> list[str]:
        stmt = select(SupervisorZona.zona).where(
            SupervisorZona.supervisor_id == supervisor_id
        )
        return list(self.db.scalars(stmt).all())

    def tiene_zona(self, supervisor_id: int, zona: str) -> bool:
        stmt = select(SupervisorZona).where(
            SupervisorZona.supervisor_id == supervisor_id,
            SupervisorZona.zona == zona,
        )
        return self.db.scalars(stmt).first() is not None

    def add(self, supervisor: Supervisor) -> Supervisor:
        self.db.add(supervisor)
        self.db.flush()
        return supervisor

    def add_zona(self, zona: SupervisorZona) -> SupervisorZona:
        self.db.add(zona)
        self.db.flush()
        return zona

    def delete(self, supervisor: Supervisor) -> None:
        self.db.delete(supervisor)

    def commit(self) -> None:
        self.db.commit()
