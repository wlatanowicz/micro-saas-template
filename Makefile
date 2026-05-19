SHELL := /bin/bash

.PHONY: help docker-start migrate make-migrations check test test-be test-be-ci lint-be

# Ephemeral Postgres for `make test-be` (avoid colliding with a local dev DB)
TEST_DB_PORT ?= 5433
TEST_DB_PASSWORD ?= postgres

.DEFAULT_GOAL := help

help: ## Print help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

docker-start: ## Start Docker Compose stack (foreground)
	docker compose up --build

migrate: ## Apply Alembic migrations inside running backend container
	docker compose exec backend uv run alembic upgrade head

make-migrations: ## Autogenerate Alembic revision inside running backend container
	docker compose exec backend uv run alembic revision --autogenerate

test-be: ## Run backend tests with ephemeral Postgres (Docker; migrations run inside pytest)
	set -euo pipefail; \
	docker rm -f micro-saas-test-db 2>/dev/null || true; \
	docker run -d --rm --name micro-saas-test-db -p $(TEST_DB_PORT):5432 \
	  -e POSTGRES_PASSWORD=$(TEST_DB_PASSWORD) postgres:18; \
	trap 'docker kill micro-saas-test-db 2>/dev/null || true' EXIT; \
	for _ in $$(seq 1 60); do \
	  docker exec micro-saas-test-db pg_isready -U postgres >/dev/null 2>&1 && break; \
	  sleep 0.5; \
	done; \
	docker exec micro-saas-test-db pg_isready -U postgres >/dev/null; \
	export DATABASE_URL=postgresql://postgres:$(TEST_DB_PASSWORD)@127.0.0.1:$(TEST_DB_PORT)/postgres; \
	export SYNC_TEST_DB_URL="$$DATABASE_URL"; \
	export JWT_SECRET=test-jwt-secret-key-at-least-thirty-two-chars-for-local-and-ci; \
	cd backend && uv run pytest

test-be-ci: ## Run backend tests using DATABASE_URL from the environment (migrations run inside pytest)
	set -euo pipefail; \
	if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi; \
	export SYNC_TEST_DB_URL="$$DATABASE_URL"; \
	export JWT_SECRET=$${JWT_SECRET:-test-jwt-secret-key-at-least-thirty-two-chars-for-local-and-ci}; \
	cd backend && uv run pytest

lint-be: ## Run Ruff on backend Python tree
	cd backend && uv run ruff check src tests conftest.py

test: test-be ## Run automated tests (backend integration suite; no frontend test script yet)

check: ## Run backend Postgres tests, Ruff, and Lambda requirements export (CI parity subset)
	$(MAKE) test-be
	$(MAKE) lint-be
	cd backend && uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements-lambda.txt
