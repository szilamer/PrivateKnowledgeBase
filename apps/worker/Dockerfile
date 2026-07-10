FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml ./
COPY packages/ ./packages/
COPY apps/ ./apps/

WORKDIR /app/apps/worker

RUN uv sync --no-dev

CMD ["uv", "run", "celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "-Q", "ingestion,extraction,embedding,graph_projection,maintenance"]
