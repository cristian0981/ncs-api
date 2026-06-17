"""Acceso a datos de la bitácora de corridas."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bitacora import Bitacora


class BitacoraRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, registro: Bitacora) -> Bitacora:
        self.db.add(registro)
        self.db.flush()
        return registro

    def ultima(self) -> Bitacora | None:
        stmt = select(Bitacora).order_by(Bitacora.inicio.desc()).limit(1)
        return self.db.scalars(stmt).first()

    def listar(self, limit: int = 20) -> list[Bitacora]:
        stmt = select(Bitacora).order_by(Bitacora.inicio.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def commit(self) -> None:
        self.db.commit()
