import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RunStatus(StrEnum):
    pending = "pending"
    producing = "producing"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class RunMode(StrEnum):
    audit = "audit"
    benchmark = "benchmark"
    simulation = "simulation"


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), default=RunStatus.pending, index=True
    )
    mode: Mapped[RunMode] = mapped_column(Enum(RunMode))
    job_count: Mapped[int] = mapped_column(BigInteger)
    producer_concurrency: Mapped[int] = mapped_column(Integer)
    target_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workload: Mapped[str] = mapped_column(String(50))
    duration_ms: Mapped[int] = mapped_column(Integer)
    failure_probability: Mapped[float] = mapped_column(Float)
    max_retries: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (Index("ix_snapshots_run_recorded", "run_id", "recorded_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_runs.id", ondelete="CASCADE")
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB)
    run: Mapped[BenchmarkRun] = relationship(back_populates="snapshots")


class ErrorSample(Base):
    __tablename__ = "error_samples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_runs.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    worker_id: Mapped[str] = mapped_column(String(200))
    attempt: Mapped[int] = mapped_column(Integer)
    error_type: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
