.PHONY: up down build logs test lint format frontend-test integration-test verify

up:
	docker compose up --build

down:
	docker compose down --remove-orphans

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm api mypy app

format:
	docker compose run --rm api ruff format .
	docker compose run --rm api ruff check --fix .

frontend-test:
	docker run --rm -v "$(CURDIR)/frontend:/app" -w /app node:22-alpine \
		sh -c "npm ci && npm test -- --run"

integration-test:
	python -m pytest tests/e2e -q

verify: lint test frontend-test
