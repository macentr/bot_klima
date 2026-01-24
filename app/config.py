from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration.

    IMPORTANT:
    - Keep all environment-specific values in env vars (no hardcoding).
    - Use DATABASE_URL like:
      postgresql+asyncpg://user:pass@host:5432/dbname
    """

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    bot_token: str
    database_url: str

    # Worker polling interval for closing events (seconds)
    event_closer_interval_seconds: int = 10


def load_settings() -> Settings:
    return Settings()

