FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
COPY packages/ ./packages/
COPY apps/ ./apps/

WORKDIR /app/apps/api

RUN uv sync --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000"]
