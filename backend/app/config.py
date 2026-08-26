from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Distributed Job Processing System"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://job_platform@localhost:5432/job_platform"
    rabbitmq_url: str = "amqp://guest@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    public_max_jobs: int = Field(default=1_000_000, ge=1, le=100_000_000)
    metrics_flush_interval_seconds: float = Field(default=2.0, gt=0, le=60)
    worker_prefetch: int = Field(default=32, ge=1, le=1_000)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
