"""Modelos de Contratista y sus correos.

Los correos van en tabla aparte porque el personal del contratista rota y a
veces hay un correo para 'lectura' y otro para 'órdenes de servicio'. Así se
puede tener varios correos activos por contratista.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Contratista(Base):
    __tablename__ = "contratistas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    nit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    correos: Mapped[list["CorreoContratista"]] = relationship(
        back_populates="contratista",
        cascade="all, delete-orphan",
    )


class CorreoContratista(Base):
    __tablename__ = "correos_contratista"

    id: Mapped[int] = mapped_column(primary_key=True)
    contratista_id: Mapped[int] = mapped_column(
        ForeignKey("contratistas.id", ondelete="CASCADE"), index=True
    )
    correo: Mapped[str] = mapped_column(String(200), index=True)
    nombre_contacto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rol: Mapped[str | None] = mapped_column(String(100), nullable=True)  # p.ej. "Lectura"
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    contratista: Mapped["Contratista"] = relationship(back_populates="correos")
