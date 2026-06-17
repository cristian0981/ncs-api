"""Servicio de auditoría: sincroniza NCs, recalcula plazos y registra bitácora.

Esta es la orquestación principal del bot. En esta primera versión:
  1) Sincroniza las NC desde la BD de origen (si está configurada).
  2) Recalcula el semáforo y los estados de TODAS las NC en control.
  3) Registra el resultado en la bitácora.

La verificación de correo (Microsoft Graph) se conecta en la Semana 2 dentro
del paso `_verificar_correos`, que hoy es un punto de extensión.

IMPORTANTE: el bot NO envía notificaciones a los contratistas. Solo audita y
deja en evidencia las NC sin notificar para que el supervisor actúe.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core import sla
from app.core.logging import get_logger
from app.db.origin import get_origin_engine
from app.models.bitacora import Bitacora
from app.models.control_nc import ControlNC
from app.models.enums import EstadoNotificacion, TipoCorrida
from app.repositories.bitacora_repository import BitacoraRepository
from app.repositories.nc_repository import NCRepository
from app.repositories.origin_repository import OriginNCRepository

logger = get_logger(__name__)


class AuditoriaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.nc_repo = NCRepository(db)
        self.bitacora_repo = BitacoraRepository(db)

    def ejecutar(self) -> Bitacora:
        """Corre el ciclo completo de auditoría y devuelve el registro de bitácora."""
        registro = Bitacora(tipo=TipoCorrida.AUDITORIA, inicio=datetime.now())
        try:
            nuevas = self._sincronizar_origen()
            procesadas, con_alerta = self._recalcular_estados()

            registro.nc_nuevas = nuevas
            registro.nc_procesadas = procesadas
            registro.nc_con_alerta = con_alerta
            registro.estado = "OK"
            registro.detalle = (
                f"Sincronización: {nuevas} nuevas. "
                f"Recalculadas: {procesadas}. Con alerta: {con_alerta}."
            )
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            registro.estado = "ERROR"
            registro.detalle = f"Error en auditoría: {exc}"
            logger.exception("Falló la auditoría")
        finally:
            registro.fin = datetime.now()
            self.bitacora_repo.add(registro)
            self.bitacora_repo.commit()
        return registro

    # --- Paso 1: sincronizar desde la BD de origen ---
    def _sincronizar_origen(self) -> int:
        engine = get_origin_engine()
        if engine is None:
            return 0

        from app.db.origin import _SessionOrigin  # sesión ya inicializada

        origin_db = _SessionOrigin() if _SessionOrigin else None
        nuevas = 0
        try:
            filas = OriginNCRepository(origin_db).fetch_nc()
            for fila in filas:
                if self._existe(fila):
                    continue
                self.nc_repo.add(self._a_modelo(fila))
                nuevas += 1
            self.nc_repo.commit()
        finally:
            if origin_db:
                origin_db.close()
        return nuevas

    def _existe(self, fila: dict) -> bool:
        return (
            self.nc_repo.find_by_llave(
                numero_archivo_soporte=fila.get("numero_archivo_soporte"),
                numero_orden_interventoria=fila.get("numero_orden_interventoria"),
                numero_orden_trabajo=fila.get("numero_orden_trabajo"),
            )
            is not None
        )

    @staticmethod
    def _a_modelo(fila: dict) -> ControlNC:
        return ControlNC(
            numero_orden_trabajo=fila.get("numero_orden_trabajo"),
            numero_orden_interventoria=fila.get("numero_orden_interventoria"),
            numero_medidor=fila.get("numero_medidor"),
            numero_archivo_soporte=fila.get("numero_archivo_soporte"),
            zona=fila.get("zona"),
            sector=fila.get("sector"),
            tipo_actividad=fila.get("tipo_actividad"),
            tipificacion=fila.get("tipificacion"),
            observacion=fila.get("observacion"),
            fecha_ejecucion=fila.get("fecha_ejecucion"),
        )

    # --- Paso 2: recalcular semáforo y estados ---
    def _recalcular_estados(self, hoy: date | None = None) -> tuple[int, int]:
        hoy = hoy or date.today()
        ncs = self.nc_repo.list_all()
        con_alerta = 0
        for nc in ncs:
            semaforo = sla.semaforo_notificacion(
                nc.fecha_ejecucion, nc.fecha_notificacion, hoy
            )
            nc.semaforo = semaforo.value
            nc.estado_notificacion = self._estado_notificacion(nc, semaforo)
            if semaforo in (sla.Semaforo.ROJO, sla.Semaforo.AMARILLO):
                con_alerta += 1
        self.nc_repo.commit()
        return len(ncs), con_alerta

    @staticmethod
    def _estado_notificacion(nc: ControlNC, semaforo) -> EstadoNotificacion:
        if nc.correo_verificado and nc.fecha_notificacion is not None:
            return EstadoNotificacion.NOTIFICADA
        if semaforo == sla.Semaforo.ROJO:
            return EstadoNotificacion.VENCIDA
        return EstadoNotificacion.PENDIENTE

    # --- Punto de extensión: verificación de correo (Semana 2) ---
    def _verificar_correos(self) -> None:
        """Pendiente: integrar Microsoft Graph para confirmar envío real."""
        raise NotImplementedError("Verificación de correo: pendiente (Semana 2).")
