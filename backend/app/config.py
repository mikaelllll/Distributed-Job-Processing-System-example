from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Distributed Job Processing System"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://job_platform:job_platform@localhost:5432/job_platform"
    rabbitmq_url: str = "amqp://job_platform:job_platform@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    public_max_jobs: int = 1_000_000
    metrics_flush_interval_seconds: float = 2.0
    worker_prefetch: int = 32

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
