# Testing and continuous integration

The project uses layered verification so defects are caught at the cheapest useful boundary and cross-service assumptions are still exercised against real infrastructure.

## Test layers

| Layer | Coverage |
| --- | --- |
| Backend unit tests | Validation, settings, workloads, counters, reconciliation, cancellation, resumption, and latency calculations |
| Frontend unit tests | Diagnosis logic, metric merging, chronology, deduplication, and terminal-state behavior |
| Static analysis | Ruff, formatting, strict mypy, ESLint, and TypeScript compilation |
| Build checks | Backend and frontend production container targets |
| Integration tests | Real PostgreSQL, Redis, RabbitMQ, API, generator, dispatcher, aggregator, and workers |
| Security audits | Python dependency audit and production npm dependency audit |

Integration scenarios cover every real workload and mode, retry and dead-letter behavior, simulation boundaries, cancellation, deletion, health endpoints, accounting invariants, unknown streams, and stream termination.

## GitHub Actions

The complete workflow runs:

- on every pull request;
- on every push to `main`;
- on a weekly schedule;
- through manual `workflow_dispatch`.

Failed integration jobs upload container logs to make diagnosis possible. Dependabot separately proposes updates for Python, npm, GitHub Actions, and Docker dependencies.

## Local commands

```bash
make test
make lint
make frontend-test
```

Run end-to-end tests against an already-running stack:

```bash
python -m pytest tests/e2e -q
```

Validate the Compose definition and build production images:

```bash
docker compose config
docker compose build
```

## Completion criterion

Passing unit tests alone is not sufficient for a distributed system. A change is considered safe only when static checks, production builds, and integration scenarios agree that lifecycle state and accounting remain consistent.
