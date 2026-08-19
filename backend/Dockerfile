# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.4

# Copy dependencies
COPY pyproject.toml poetry.lock ./

# Install dependencies in project virtualenv
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-interaction --no-ansi --only main --no-root

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Copy only the virtualenv from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy specific application code directories
COPY pyproject.toml poetry.lock ./
COPY core ./core
COPY api ./api
COPY agents ./agents
COPY brain ./brain

# Setup non-root user for security
RUN useradd -m -u 1001 appuser
USER 1001

# Expose port
EXPOSE 8080

# Start command
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8080"]
