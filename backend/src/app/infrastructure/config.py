"""Configuracion de la aplicacion leida del entorno."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes del servicio.

    Todos los valores provienen de variables de entorno o de un archivo .env,
    nunca del codigo fuente. Los secretos no se versionan.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Medical Appointment API"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    database_url: str = Field(default="sqlite+pysqlite:///./medical.db")

    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None

    otel_enabled: bool = Field(default=False)
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")

    @property
    def notifications_enabled(self) -> bool:
        """Indica si hay credenciales suficientes para enviar WhatsApp."""
        return all((self.twilio_account_sid, self.twilio_auth_token, self.twilio_whatsapp_from))


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuracion, cacheada para no releer el entorno."""
    return Settings()
