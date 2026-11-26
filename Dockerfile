# Dockerfile
FROM python:3.14-slim

# Copy the uv binary from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first, so this layer is cached until pyproject or the lock changes
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

# Then copy the source and install the project itself
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini README.md ./
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn forest_ai.main:app --host 0.0.0.0 --port 8000"]