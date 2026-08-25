# ADR 0001: Separate broker, durable storage, and live aggregation

Status: Accepted

## Decision

Use RabbitMQ for job delivery, PostgreSQL for durable business state, and Redis for ephemeral counters and coordination.

## Rationale

Each system is used for the guarantee it provides best. RabbitMQ exposes acknowledgments and dead-letter routing. PostgreSQL supports transactional state and history. Redis permits high-frequency atomic updates without turning the primary database into the benchmark bottleneck.

## Consequences

The local stack has more services, but failure modes and scaling boundaries remain explicit. Redis loss affects live telemetry but not saved run definitions or completed reports.

