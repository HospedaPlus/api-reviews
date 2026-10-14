from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "HospedaPlus Reviews API (F5)"
    app_version: str = "0.1.0"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/reviews"

    # Pagination limits exposed to consumers (ingestion jobs, BI, etc.)
    default_page_size: int = 50
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
