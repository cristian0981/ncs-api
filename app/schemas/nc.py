"""Esquemas de No Conformidad (lectura, alertas, estadisticas y filtros)."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class NCRead(BaseModel):
    """Vista detallada de una NC en control."""

    id: int
    numero_orden_trabajo: str | None = None
    numero_orden_interventoria: str | None = None
    numero_medidor: str | None = None
    numero_archivo_soporte: str | None = None

    zona: str | None = None
    sector: str | None = None
    tipo_actividad: str | None = None

    tipificacion: str | None = None
    observacion: str | None = None
    fecha_ejecucion: date | None = None
    contratista_id: int | None = None

    fecha_notificacion: date | None = None
    correo_verificado: bool = False
    soporte_adjunto_ok: bool = False

    fecha_respuesta_contratista: date | None = None
    fecha_validacion_ises: date | None = None

    estado_notificacion: str
    estado_nc: str
    semaforo: str

    model_config = {"from_attributes": True}


class NCAlerta(BaseModel):
    """Fila de la tabla de alertas (NCs criticas / por vencer)."""

    id: int
    zona: str | None = None
    sector: str | None = None
    tipo_actividad: str | None = None
    numero_orden_interventoria: str | None = None
    contratista_id: int | None = None
    fecha_ejecucion: date | None = None
    fecha_limite_notificacion: date | None = None
    dias_restantes: int | None = None
    estado_notificacion: str
    semaforo: str
    motivo: str

    model_config = {"from_attributes": True}


class SemaforoConteo(BaseModel):
    verde: int = 0
    amarillo: int = 0
    rojo: int = 0
    sin_dato: int = 0


class NCStats(BaseModel):
    """Tarjetas del dashboard."""

    total: int
    notificadas: int
    pendientes: int
    vencidas: int
    sin_verificar_correo: int
    por_zona: dict[str, int]
    por_sector: dict[str, int]
    por_tipo_actividad: dict[str, int]
    semaforo_notificacion: SemaforoConteo


class FiltrosDisponibles(BaseModel):
    """Valores disponibles para poblar los filtros (zona, sector, actividad)."""

    zonas: list[str]
    sectores: list[str]
    tipos_actividad: list[str]
