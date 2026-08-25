# Architecture overview

Dispatch separates command handling, durable storage, message delivery, job execution, and live telemetry so each component can scale and fail independently.

## Data flow

1. The API validates a benchmark and writes both the run and an outbox event in one PostgreSQL transaction.
2. The outbox dispatcher publishes confirmed control messages to RabbitMQ.
3. The load generator consumes the control message and publishes durable job messages at the requested rate.
4. Workers acknowledge messages only after execution and metric updates. Failures enter TTL-backed retry queues and eventually the dead-letter queue.
5. Workers update atomic Redis counters. The aggregator derives rates and latency percentiles, persists snapshots to PostgreSQL, and marks completed runs.
6. The React client receives one-second metric snapshots over Server-Sent Events.

## Delivery guarantee

The worker path provides at-least-once delivery. Handlers must therefore be idempotent. RabbitMQ acknowledgments, durable queues, persistent messages, publisher confirms, and the transactional outbox jointly prevent common message-loss windows.

## Storage policy

- PostgreSQL is the durable system of record.
- RabbitMQ transports work; it is not a database.
- Redis holds reconstructable live state and coordination data.
- Prometheus holds operational time series.

## Scale modes

Audit mode is intended for traceable production-style workloads. Benchmark mode stores aggregates and error samples. Simulation mode models extreme logical workloads without claiming to execute every job.

