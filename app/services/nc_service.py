"""Logica de negocio de No Conformidades: estadisticas, alertas y filtros."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core import sla
from app.core.sla import Semaforo
from app.models.control_nc import ControlNC
from app.models.enums import EstadoNotificacion
from app.repositories.nc_repository import NCRepository
from app.repositories.supervisor_repository import SupervisorRepository
from app.schemas.nc import FiltrosDisponibles, NCAlerta, NCStats, SemaforoConteo


class NCService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NCRepository(db)

    # --- Lectura ---
    def get(self, nc_id: int) -> ControlNC | None:
        return self.repo.get(nc_id)

    def list(
        self,
        *,
        supervisor_id: int | None = None,
        zona: str | None = None,
        sector: str | None = None,
        tipo_actividad: str | None = None,
        estado_notificacion: str | None = None,
        semaforo: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ControlNC]:
        # Si llega un supervisor, su alcance son las zonas que tiene asignadas.
        zonas = None
        if supervisor_id is not None:
            zonas = SupervisorRepository(self.db).zonas_de(supervisor_id)
        return self.repo.list(
            zona=zona,
            zonas=zonas,
            sector=sector,
            tipo_actividad=tipo_actividad,
            estado_notificacion=estado_notificacion,
            semaforo=semaforo,
            skip=skip,
            limit=limit,
        )

    # --- Filtros disponibles (valores presentes en la base local) ---
    def get_filtros(self) -> FiltrosDisponibles:
        return FiltrosDisponibles(
            zonas=self.repo.zonas_disponibles(),
            sectores=self.repo.sectores_disponibles(),
            tipos_actividad=self.repo.tipos_actividad_disponibles(),
        )

    # --- Estadisticas (dashboard) ---
    def get_stats(self) -> NCStats:
        conteo_sem = self.repo.contar_por_semaforo()
        return NCStats(
            total=self.repo.total(),
            notificadas=self.repo.contar_por_estado(EstadoNotificacion.NOTIFICADA),
            pendientes=self.repo.contar_por_estado(EstadoNotificacion.PENDIENTE),
            vencidas=self.repo.contar_por_estado(EstadoNotificacion.VENCIDA),
            sin_verificar_correo=self.repo.contar_sin_verificar_correo(),
            por_zona=self.repo.contar_por_zona(),
            por_sector=self.repo.contar_por_sector(),
            por_tipo_actividad=self.repo.contar_por_tipo_actividad(),
            semaforo_notificacion=SemaforoConteo(
                verde=conteo_sem.get(Semaforo.VERDE, 0),
                amarillo=conteo_sem.get(Semaforo.AMARILLO, 0),
                rojo=conteo_sem.get(Semaforo.ROJO, 0),
                sin_dato=conteo_sem.get(Semaforo.SIN_DATO, 0),
            ),
        )

    # --- Alertas (NCs en rojo / amarillo) ---
    def get_alertas(self, hoy: date | None = None) -> list[NCAlerta]:
        hoy = hoy or date.today()
        criticas = self.repo.list_por_semaforo([Semaforo.ROJO, Semaforo.AMARILLO])
        alertas: list[NCAlerta] = []
        for nc in criticas:
            limite = (
                sla.fecha_limite_notificacion(nc.fecha_ejecucion)
                if nc.fecha_ejecucion
                else None
            )
            dias_restantes = (limite - hoy).days if limite else None
            alertas.append(
                NCAlerta(
                    id=nc.id,
                    zona=nc.zona,
                    sector=nc.sector,
                    tipo_actividad=nc.tipo_actividad,
                    numero_orden_interventoria=nc.numero_orden_interventoria,
                    contratista_id=nc.contratista_id,
                    fecha_ejecucion=nc.fecha_ejecucion,
                    fecha_limite_notificacion=limite,
                    dias_restantes=dias_restantes,
                    estado_notificacion=nc.estado_notificacion,
                    semaforo=nc.semaforo,
                    motivo=self._motivo(nc, dias_restantes),
                )
            )
        alertas.sort(key=lambda a: (a.dias_restantes is None, a.dias_restantes or 0))
        return alertas

    @staticmethod
    def _motivo(nc: ControlNC, dias_restantes: int | None) -> str:
        if nc.estado_notificacion == EstadoNotificacion.VENCIDA:
            return "Plazo de notificacion vencido sin correo verificado"
        if not nc.correo_verificado:
            if dias_restantes is not None and dias_restantes < 0:
                return "Sin notificar y fuera de plazo"
            return f"Sin notificar; quedan {dias_restantes} dia(s)"
        return "Pendiente de revision"
