.PHONY: help up down build logs migrate test lint typecheck ci dev-setup

COMPOSE_FILE := infra/docker/docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

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

dev-setup:
	uv sync --all-packages
	cd apps/web && npm install

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec api alembic upgrade head

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check apps packages tests
	uv run ruff format --check apps packages tests

typecheck:
	uv run mypy

ci: lint typecheck test
