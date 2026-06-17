"""Lectura de la BD de ORIGEN (Formap), motor SQL Server.

Extrae las actividades calificadas como NC, con posibilidad de filtrar por
zona, sector y tipo de actividad. La consulta usa texto SQL parametrizado por
configuracion. Como el esquema real de Formap aun no esta confirmado, los
nombres de columna se mapean en un unico punto (`_COLUMNAS`).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mapeo columna logica -> columna real en la BD de origen (ajustar al confirmar Formap).
_COLUMNAS: dict[str, str] = {
    "numero_orden_trabajo": "orden_trabajo",
    "numero_orden_interventoria": "orden_interventoria",
    "numero_medidor": "medidor",
    "numero_archivo_soporte": "archivo_soporte",
    "zona": "zona",
    "sector": "sector",
    "tipo_actividad": "tipo_actividad",
    "tipificacion": "tipificacion",
    "observacion": "observacion",
    "fecha_ejecucion": "fecha_ejecucion",
    "contratista": "contratista",
}


class OriginNCRepository:
    def __init__(self, db: Session | None) -> None:
        self.db = db

    def disponible(self) -> bool:
        return self.db is not None and settings.origin_db_configured

    def fetch_nc(
        self,
        *,
        zonas: list[str] | None = None,
        sector: str | None = None,
        tipo_actividad: str | None = None,
    ) -> list[dict[str, Any]]:
        """Devuelve las actividades NC (opcionalmente filtradas) como diccionarios."""
        if not self.disponible():
            logger.warning("BD de origen no disponible: se devuelve lista vacia.")
            return []

        selects = ", ".join(f"{col} AS {alias}" for alias, col in _COLUMNAS.items())
        where = ["calificacion = :calif"]
        params: dict[str, Any] = {"calif": settings.ORIGIN_NC_CALIFICACION_VALUE}

        if zonas:
            marcadores = ", ".join(f":zona_{i}" for i in range(len(zonas)))
            where.append(f"{_COLUMNAS['zona']} IN ({marcadores})")
            params.update({f"zona_{i}": z for i, z in enumerate(zonas)})
        if sector:
            where.append(f"{_COLUMNAS['sector']} = :sector")
            params["sector"] = sector
        if tipo_actividad:
            where.append(f"{_COLUMNAS['tipo_actividad']} = :tipo")
            params["tipo"] = tipo_actividad

        sql = text(
            f"SELECT {selects} FROM {settings.ORIGIN_NC_TABLE} "
            f"WHERE {' AND '.join(where)}"
        )
        rows = self.db.execute(sql, params)
        return [dict(row._mapping) for row in rows]

    def valores_distintos(self, columna_logica: str) -> list[str]:
        """Lista los valores distintos de una columna (zona/sector/tipo_actividad)."""
        if not self.disponible() or columna_logica not in _COLUMNAS:
            return []
        col = _COLUMNAS[columna_logica]
        sql = text(
            f"SELECT DISTINCT {col} FROM {settings.ORIGIN_NC_TABLE} "
            f"WHERE {col} IS NOT NULL ORDER BY {col}"
        )
        return [row[0] for row in self.db.execute(sql) if row[0]]
