.PHONY: help up down build logs migrate test lint typecheck ci dev-setup backup restore rebuild-projection load-smoke

COMPOSE_FILE := infra/docker/docker-compose.yml
COMPOSE_OVERRIDE := infra/docker/docker-compose.override.generated.yml
COMPOSE := docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_OVERRIDE)

help:
	@echo "Private Knowledge Base — development commands"
	@echo ""
	@echo "  make dev-setup   Install local Python and Node dependencies"
	@echo "  make up          Start all services (Docker Compose)"
	@echo "  make down        Stop all services"
	@echo "  make build       Build Docker images"
	@echo "  make logs        Tail service logs"
	@echo "  make migrate     Run Alembic migrations"
	@echo "  make test        Run test suite"
	@echo "  make lint        Run Ruff linter"
	@echo "  make typecheck   Run mypy"
	@echo "  make ci          Run full local CI checks"
	@echo "  make backup      Dump PostgreSQL to backups/"
	@echo "  make restore     Restore PostgreSQL (BACKUP=path required)"
	@echo "  make rebuild-projection  Rebuild Neo4j from canonical PostgreSQL"
	@echo "  make load-smoke  Run API health load smoke (stack must be up)"

dev-setup:
	uv sync --all-packages
	cd apps/web && npm install

up:
	chmod +x infra/scripts/prepare-host-sources.sh
	./infra/scripts/prepare-host-sources.sh
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

migrate:
	@set -a && [ -f .env ] && . ./.env && set +a; \
	PG_HOST=$$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1); \
	cd apps/api && DATABASE_URL="postgresql+asyncpg://$${POSTGRES_USER:-pkb}:$${POSTGRES_PASSWORD:-change-me-in-production}@$$PG_HOST:5432/$${POSTGRES_DB:-pkb}" uv run alembic upgrade head

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check apps packages tests
	uv run ruff format --check apps packages tests

typecheck:
	uv run mypy

ci: lint typecheck test

backup:
	chmod +x infra/scripts/backup.sh
	./infra/scripts/backup.sh

restore:
	@test -n "$(BACKUP)" || (echo "Usage: make restore BACKUP=backups/<timestamp>" && exit 1)
	chmod +x infra/scripts/restore.sh
	./infra/scripts/restore.sh "$(BACKUP)"

rebuild-projection:
	curl -sf -X POST http://localhost:8000/api/v1/operations/projection/rebuild

load-smoke:
	chmod +x infra/scripts/load_smoke.sh
	./infra/scripts/load_smoke.sh

e2e-smoke:
	chmod +x infra/scripts/e2e_smoke.sh
	./infra/scripts/e2e_smoke.sh
