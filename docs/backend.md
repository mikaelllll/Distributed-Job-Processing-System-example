# Backend

The backend is a set of cooperating Python services rather than a single request-processing application. Separating coordination, production, execution, and aggregation makes failure behavior visible and allows each responsibility to scale independently.

## Services

| Service | Responsibility |
| --- | --- |
| API | Validates commands, creates and queries runs, streams metrics, cancels and deletes runs |
| Outbox dispatcher | Reliably publishes committed run commands to RabbitMQ |
| Load generator | Produces deterministic jobs at controlled concurrency and rate |
| Workers | Execute workloads, acknowledge messages, retry transient failures, and dead-letter exhausted jobs |
| Metrics aggregator | Reconciles Redis live counters and persists chronological snapshots |

## Persistence responsibilities

PostgreSQL is the durable source of truth for run definitions, outbox records, lifecycle state, and final reports. Redis stores high-frequency counters, cancellation state, worker heartbeats, and other disposable live data. RabbitMQ transports commands and jobs.

This separation prevents frequent metrics updates from turning PostgreSQL into the throughput bottleneck while retaining durable completed results.

## Delivery and idempotency

The platform uses at-least-once delivery. A worker acknowledges a RabbitMQ delivery only after processing. Consequently, any real-world handler added to the platform must be idempotent.

Generated job identifiers are deterministic for a run and job index. This lets an interrupted producer resume without inventing a second identity for the same logical job. The generator stores progress in Redis and resumes runs left in producing or pending states.

## Retries and dead letters

Failed jobs enter TTL-backed retry queues and return after the configured delay. Retry exhaustion moves the job to a dead-letter queue and records it as permanently failed. Retry attempts are distinct from final errors in the dashboard.

## Cancellation and deletion

Cancellation state is shared through Redis. Producers and workers check it so deleting a running test stops additional useful work rather than merely removing its history row. Deletion also removes the persisted run after cancellation has been requested.

## API access

Interactive OpenAPI documentation is available on port 8000 at `/docs`. The dashboard uses REST for commands and historical data, plus Server-Sent Events for live run metrics. A stream for an unknown run returns `404`, and completed streams terminate instead of appending flat samples forever.

## Validation and configuration

Pydantic models enforce workload boundaries and normalize input such as run names and CORS origins. Settings come from environment variables; committed configuration contains placeholders only. Database schema changes are managed with Alembic.
