"""Configuracion central de la aplicacion.

Carga las variables de entorno (archivo .env) y las expone como un objeto
`settings` tipado. Usar siempre `from app.core.config import settings`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Bot Control NC - Celsia/ISES"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # --- CORS ---
    # Se guarda como texto (separado por comas) para evitar que pydantic-settings
    # intente parsearlo como JSON desde el .env. Usar `settings.cors_origins`.
    BACKEND_CORS_ORIGINS: str = "http://localhost:4200"

    # --- Bases de datos ---
    LOCAL_DATABASE_URL: str = "sqlite:///./data/control_nc.db"
    ORIGIN_DATABASE_URL: str = ""
    ORIGIN_NC_TABLE: str = "actividades"
    ORIGIN_NC_CALIFICACION_VALUE: str = "NC"

    # --- SLA ---
    SLA_DIAS_NOTIFICACION: int = 8
    SLA_DIAS_VALIDACION_ISES: int = 5
    SLA_PAIS_FESTIVOS: str = "CO"

    # --- Microsoft Graph ---
    GRAPH_TENANT_ID: str = ""
    GRAPH_CLIENT_ID: str = ""
    GRAPH_CLIENT_SECRET: str = ""
    GRAPH_BOT_MAILBOX: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Lista de origenes permitidos para CORS (separados por comas)."""
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def origin_db_configured(self) -> bool:
        """True cuando ya se configuro la conexion a la BD de origen (Formap)."""
        return bool(self.ORIGIN_DATABASE_URL.strip())

    @property
    def graph_configured(self) -> bool:
        """True cuando las credenciales de Microsoft Graph estan completas."""
        return all(
            [self.GRAPH_TENANT_ID, self.GRAPH_CLIENT_ID, self.GRAPH_CLIENT_SECRET]
        )


@lru_cache
def get_settings() -> Settings:
    """Devuelve una unica instancia de Settings (cacheada)."""
    return Settings()


settings = get_settings()
