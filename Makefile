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
	docker build --target test -t distributed-job-platform-backend-test backend
	docker run --rm distributed-job-platform-backend-test

lint:
	docker build --target test -t distributed-job-platform-backend-test backend
	docker run --rm distributed-job-platform-backend-test ruff check .
	docker run --rm distributed-job-platform-backend-test mypy app

format:
	docker build --target test -t distributed-job-platform-backend-test backend
	docker run --rm -v "$(CURDIR)/backend:/app" distributed-job-platform-backend-test ruff format .
	docker run --rm -v "$(CURDIR)/backend:/app" distributed-job-platform-backend-test ruff check --fix .

frontend-test:
	docker build --target test -t distributed-job-platform-frontend-test frontend
	docker run --rm distributed-job-platform-frontend-test

integration-test:
	python -m pytest tests/e2e -q

verify: lint test frontend-test
