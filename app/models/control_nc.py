"""Modelo central: control de cada No Conformidad.

Combina los datos que vienen de la BD de origen (Formap) con la evidencia que
el bot verifica en el correo y los plazos calculados por el motor SLA.

Las tres dimensiones de filtro (zona, sector y tipo de actividad) vienen de
Formap y permiten acotar las NC que se muestran y se sincronizan.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.contratista import Contratista
from app.models.enums import EstadoNC, EstadoNotificacion


class ControlNC(Base):
    __tablename__ = "control_nc"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Identificadores (llaves para el cruce plano/informe/correo) ---
    numero_orden_trabajo: Mapped[str | None] = mapped_column(String(80), index=True)
    numero_orden_interventoria: Mapped[str | None] = mapped_column(String(80), index=True)
    numero_medidor: Mapped[str | None] = mapped_column(String(80), index=True)
    numero_archivo_soporte: Mapped[str | None] = mapped_column(String(120), index=True)

    # --- Dimensiones de filtro (desde Formap) ---
    zona: Mapped[str | None] = mapped_column(String(120), index=True)
    sector: Mapped[str | None] = mapped_column(String(120), index=True)
    tipo_actividad: Mapped[str | None] = mapped_column(String(120), index=True)

    # --- Datos de la NC (desde la BD de origen) ---
    tipificacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_ejecucion: Mapped[date | None] = mapped_column(Date, nullable=True)

    contratista_id: Mapped[int | None] = mapped_column(
        ForeignKey("contratistas.id"), nullable=True, index=True
    )

    # --- Evidencia / verificacion de correo (Fase 3) ---
    fecha_notificacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    correo_verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    correo_mensaje_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    soporte_adjunto_ok: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Respuesta del contratista y validacion ISES ---
    fecha_respuesta_contratista: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_validacion_ises: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Estados derivados ---
    estado_notificacion: Mapped[EstadoNotificacion] = mapped_column(
        String(20), default=EstadoNotificacion.PENDIENTE
    )
    estado_nc: Mapped[EstadoNC] = mapped_column(String(20), default=EstadoNC.EN_CURSO)
    semaforo: Mapped[str] = mapped_column(String(12), default="SIN_DATO")

    # --- Trazabilidad ---
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    contratista: Mapped["Contratista | None"] = relationship()
