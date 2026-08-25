import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import RunMode, RunStatus


class BenchmarkCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    job_count: int = Field(ge=1, le=100_000_000)
    mode: RunMode = RunMode.benchmark
    producer_concurrency: int = Field(default=20, ge=1, le=500)
    target_rate: int | None = Field(default=None, ge=1, le=1_000_000)
    workload: Literal["io_light", "io_heavy", "cpu_light", "unreliable"] = "io_light"
    duration_ms: int = Field(default=25, ge=0, le=60_000)
    failure_probability: float = Field(default=0, ge=0, le=1)
    max_retries: int = Field(default=3, ge=0, le=10)

    @model_validator(mode="after")
    def validate_large_run(self) -> "BenchmarkCreate":
        if self.job_count > 1_000_000 and self.mode != RunMode.simulation:
            raise ValueError("Runs above 1,000,000 jobs require simulation mode")
        return self


class BenchmarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: RunStatus
    mode: RunMode
    job_count: int
    producer_concurrency: int
    target_rate: int | None
    workload: str
    duration_ms: int
    failure_probability: float
    max_retries: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    final_metrics: dict[str, Any] | None


class BenchmarkDetail(BenchmarkRead):
    snapshots: list[dict[str, Any]] = Field(default_factory=list)


class RunActionResponse(BaseModel):
    id: uuid.UUID
    status: RunStatus
