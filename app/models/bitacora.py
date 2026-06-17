"""Bitácora de corridas del bot (sincronización y auditoría)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TipoCorrida


class Bitacora(Base):
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoCorrida] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20), default="OK")  # OK | ERROR

    inicio: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    nc_procesadas: Mapped[int] = mapped_column(Integer, default=0)
    nc_nuevas: Mapped[int] = mapped_column(Integer, default=0)
    nc_con_alerta: Mapped[int] = mapped_column(Integer, default=0)

    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
