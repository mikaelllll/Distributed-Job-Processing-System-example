# Infrastructure and observability

Docker Compose is the executable system definition for development, Codespaces, testing, and demonstration. Application services use multi-stage images so production targets exclude test-only dependencies.

## Containers

| Component | Role |
| --- | --- |
| Frontend | Nginx-served React build and reverse proxy |
| API | FastAPI HTTP application |
| Dispatcher | Transactional-outbox publisher |
| Generator | Controlled job producer |
| Worker | Horizontally scalable workload consumer |
| Aggregator | Live metric reconciliation and persistence |
| PostgreSQL | Durable application state |
| RabbitMQ | Commands, jobs, retries, and dead letters |
| Redis | Atomic live state and coordination |
| Prometheus | Metrics collection |
| Grafana | Operational dashboards |

## Networking and credentials

PostgreSQL, Redis, and RabbitMQ's protocol port are reachable only inside the Compose network. User-facing management and application ports bind to localhost. Codespaces forwards selected localhost ports through its authenticated proxy.

The committed `.env.example` contains placeholders. Codespaces generates random credentials into an untracked `.env` with restrictive permissions.

## Health and startup

Compose health checks express readiness for critical dependencies and application endpoints. Startup scripts wait for the frontend and API rather than assuming that a running container is ready. Service dependencies and retry behavior allow the stack to recover from normal initialization ordering.

## Observability

Prometheus scrapes application and infrastructure metrics. Grafana provides dashboards for operational exploration. Structured backend logs provide machine-readable context, while RabbitMQ management shows queues, consumers, message rates, retries, and dead letters.

Observability is part of the demonstration: it allows a reviewer to compare what the application reports with broker and service-level behavior.

## Production boundary

The Compose stack is appropriate for an isolated demonstration, development, and integration testing. A production deployment would normally use managed data services, a secrets manager, TLS termination, authentication, authorization, backups, resource limits, network policy, alerting, and independently scalable services.
