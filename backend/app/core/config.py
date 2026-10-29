"""Environment-based configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/billing_db",
        description="PostgreSQL connection URL",
    )
    APP_ENV: str = Field(default="development", description="Application environment")
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )
    DEMO_MODE: bool = Field(default=True, description="Enable demo mode (no auth)")
    RETRY_SCHEDULE: str = Field(
        default="3,7,14",
        description="Comma-separated days between retry attempts",
    )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    def get_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def get_retry_schedule(self) -> List[int]:
        return [int(d.strip()) for d in self.RETRY_SCHEDULE.split(",") if d.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
