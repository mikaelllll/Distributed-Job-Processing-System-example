"""Initial schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_status = postgresql.ENUM(
        "pending",
        "producing",
        "running",
        "completed",
        "cancelled",
        "failed",
        name="runstatus",
        create_type=False,
    )
    run_mode = postgresql.ENUM(
        "audit", "benchmark", "simulation", name="runmode", create_type=False
    )
    run_status.create(op.get_bind(), checkfirst=True)
    run_mode.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "benchmark_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", run_status, nullable=False),
        sa.Column("mode", run_mode, nullable=False),
        sa.Column("job_count", sa.BigInteger(), nullable=False),
        sa.Column("producer_concurrency", sa.Integer(), nullable=False),
        sa.Column("target_rate", sa.Integer(), nullable=True),
        sa.Column("workload", sa.String(50), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("failure_probability", sa.Float(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_metrics", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_benchmark_runs_status", "benchmark_runs", ["status"])
    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benchmark_runs.id", ondelete="CASCADE"),
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_snapshots_run_recorded", "metric_snapshots", ["run_id", "recorded_at"])
    op.create_table(
        "error_samples",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benchmark_runs.id", ondelete="CASCADE"),
        ),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worker_id", sa.String(200), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(120), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_error_samples_run_id", "error_samples", ["run_id"])
    op.create_index("ix_error_samples_job_id", "error_samples", ["job_id"])
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_topic", "outbox_events", ["topic"])
    op.create_index("ix_outbox_events_published_at", "outbox_events", ["published_at"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("error_samples")
    op.drop_table("metric_snapshots")
    op.drop_table("benchmark_runs")
    op.execute("DROP TYPE IF EXISTS runstatus")
    op.execute("DROP TYPE IF EXISTS runmode")
