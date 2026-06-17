"""Acceso a datos de la tabla local de control de NC.

Esta capa SOLO habla con la base de datos: no contiene reglas de negocio.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.control_nc import ControlNC
from app.models.enums import EstadoNotificacion


class NCRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Consultas ---
    def get(self, nc_id: int) -> ControlNC | None:
        return self.db.get(ControlNC, nc_id)

    def list(
        self,
        *,
        zona: str | None = None,
        zonas: list[str] | None = None,
        sector: str | None = None,
        tipo_actividad: str | None = None,
        estado_notificacion: str | None = None,
        semaforo: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ControlNC]:
        stmt = self._aplicar_filtros(
            select(ControlNC),
            zona=zona,
            zonas=zonas,
            sector=sector,
            tipo_actividad=tipo_actividad,
            estado_notificacion=estado_notificacion,
            semaforo=semaforo,
        )
        stmt = stmt.order_by(ControlNC.fecha_ejecucion.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def _aplicar_filtros(
        stmt,
        *,
        zona: str | None = None,
        zonas: list[str] | None = None,
        sector: str | None = None,
        tipo_actividad: str | None = None,
        estado_notificacion: str | None = None,
        semaforo: str | None = None,
    ):
        if zonas is not None:
            # Alcance del supervisor: si no tiene zonas, no ve nada.
            stmt = stmt.where(ControlNC.zona.in_(zonas or ["__sin_zona__"]))
        if zona:
            stmt = stmt.where(ControlNC.zona == zona)
        if sector:
            stmt = stmt.where(ControlNC.sector == sector)
        if tipo_actividad:
            stmt = stmt.where(ControlNC.tipo_actividad == tipo_actividad)
        if estado_notificacion:
            stmt = stmt.where(ControlNC.estado_notificacion == estado_notificacion)
        if semaforo:
            stmt = stmt.where(ControlNC.semaforo == semaforo)
        return stmt

    def list_all(self) -> list[ControlNC]:
        return list(self.db.scalars(select(ControlNC)).all())

    def list_por_semaforo(self, semaforos: list[str]) -> list[ControlNC]:
        stmt = select(ControlNC).where(ControlNC.semaforo.in_(semaforos))
        return list(self.db.scalars(stmt).all())

    def find_by_llave(
        self,
        *,
        numero_orden_interventoria: str | None = None,
        numero_orden_trabajo: str | None = None,
        numero_archivo_soporte: str | None = None,
    ) -> ControlNC | None:
        """Busca una NC por cualquiera de las llaves del cruce."""
        stmt = select(ControlNC)
        if numero_archivo_soporte:
            stmt = stmt.where(ControlNC.numero_archivo_soporte == numero_archivo_soporte)
        elif numero_orden_interventoria:
            stmt = stmt.where(
                ControlNC.numero_orden_interventoria == numero_orden_interventoria
            )
        elif numero_orden_trabajo:
            stmt = stmt.where(ControlNC.numero_orden_trabajo == numero_orden_trabajo)
        else:
            return None
        return self.db.scalars(stmt.limit(1)).first()

    # --- Conteos para estadisticas ---
    def total(self) -> int:
        return self.db.scalar(select(func.count()).select_from(ControlNC)) or 0

    def contar_por_estado(self, estado: EstadoNotificacion) -> int:
        stmt = (
            select(func.count())
            .select_from(ControlNC)
            .where(ControlNC.estado_notificacion == estado)
        )
        return self.db.scalar(stmt) or 0

    def _contar_por_columna(self, columna) -> dict[str, int]:
        stmt = select(columna, func.count()).group_by(columna)
        return {valor: total for valor, total in self.db.execute(stmt).all() if valor}

    def contar_por_zona(self) -> dict[str, int]:
        return self._contar_por_columna(ControlNC.zona)

    def contar_por_sector(self) -> dict[str, int]:
        return self._contar_por_columna(ControlNC.sector)

    def contar_por_tipo_actividad(self) -> dict[str, int]:
        return self._contar_por_columna(ControlNC.tipo_actividad)

    def contar_por_semaforo(self) -> dict[str, int]:
        return self._contar_por_columna(ControlNC.semaforo)

    def contar_sin_verificar_correo(self) -> int:
        stmt = (
            select(func.count())
            .select_from(ControlNC)
            .where(ControlNC.correo_verificado.is_(False))
        )
        return self.db.scalar(stmt) or 0

    # --- Valores distintos para poblar filtros ---
    def _valores_distintos(self, columna) -> list[str]:
        stmt = select(columna).where(columna.is_not(None)).distinct().order_by(columna)
        return [v for v in self.db.scalars(stmt).all() if v]

    def zonas_disponibles(self) -> list[str]:
        return self._valores_distintos(ControlNC.zona)

    def sectores_disponibles(self) -> list[str]:
        return self._valores_distintos(ControlNC.sector)

    def tipos_actividad_disponibles(self) -> list[str]:
        return self._valores_distintos(ControlNC.tipo_actividad)

    # --- Escritura ---
    def add(self, nc: ControlNC) -> ControlNC:
        self.db.add(nc)
        self.db.flush()
        return nc

    def commit(self) -> None:
        self.db.commit()
