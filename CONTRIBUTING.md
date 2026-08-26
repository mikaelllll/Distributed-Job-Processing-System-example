# Contributing

## Development workflow

1. Create a branch from `main`.
2. Keep changes focused and add tests for changed behavior.
3. Run `make verify` for static checks and unit tests.
4. With the Compose stack running, run `make integration-test`.
5. Open a pull request and wait for every required CI job to pass.

Use conventional, imperative commit subjects such as `fix: reconcile terminal counters`.

## Quality expectations

- Preserve the exact accounting invariant documented in the README.
- Treat RabbitMQ delivery as at least once and keep handlers idempotent.
- Never commit `.env`, credentials, generated build output, or benchmark data.
- Document meaningful architectural trade-offs in `docs/decisions`.
- Include measured performance claims only when the methodology and environment are reproducible.
