# Stage 1: Builder
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

# Cache layer: install only main dependencies (tools group excluded to save space on Render free tier)
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root --only main


# Stage 2: Runner
FROM python:3.11-slim AS runner
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Create non-root user appuser
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only virtual environment (not full source code)
COPY --from=builder /app/.venv /app/.venv
COPY backend/ .
# Copy root-level 'skills' directory for core/evolution/auto_skill_creator.py imports
COPY skills/ ./skills/
# Copy ask_scribe.py for api/routes/knowledge.py imports
COPY ask_scribe.py ./

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
# EXPOSE port consistent with CMD's ${PORT:-8080} default
EXPOSE 8080

# Container health check — ensures Render/Cloud Run detects healthy state
# start-period 40s allows time for Python env to load on first boot
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Use main.py entrypoint for role-based boot, signal handling, and UVICORN_WORKERS support
# Note: Previously GUNICORN_WORKERS=4 default caused OOM on Render free tier (512MB RAM)
CMD ["sh", "-c", "python main.py"]
