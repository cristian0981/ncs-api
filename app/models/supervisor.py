"""Modelo de Supervisor y sus zonas asignadas.

Sin autenticacion: el supervisor es un registro del bot al que se le asignan
una o varias zonas. Con esa zona fijada, podra filtrar por sector y tipo de
actividad (valores que vienen de Formap).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Supervisor(Base):
    __tablename__ = "supervisores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    correo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    zonas: Mapped[list["SupervisorZona"]] = relationship(
        back_populates="supervisor",
        cascade="all, delete-orphan",
    )


class SupervisorZona(Base):
    __tablename__ = "supervisor_zonas"
    __table_args__ = (UniqueConstraint("supervisor_id", "zona", name="uq_supervisor_zona"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    supervisor_id: Mapped[int] = mapped_column(
        ForeignKey("supervisores.id", ondelete="CASCADE"), index=True
    )
    zona: Mapped[str] = mapped_column(String(120), index=True)

    supervisor: Mapped["Supervisor"] = relationship(back_populates="zonas")
