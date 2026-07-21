# Stage 1: Builder
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

# ক্যাশ লেয়ার: শুধু ডিপেন্ডেন্সি ইন্সটল
COPY backend/pyproject.toml backend/poetry.lock* ./
# বাংলা মন্তব্য: Render free tier-এ 'tools' group (~500MB) বাদ দেওয়া হয়েছে — শুধু main dependencies।
# chromadb, qdrant-client, sentence-transformers এখন main group-এ আছে, তাই এটাই install করবে।
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Stage 2: Runner
FROM python:3.11-slim AS runner
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# Create non-root user appuser
RUN groupadd -r appuser && useradd -r -g appuser appuser

# শুধুমাত্র ভার্চুয়াল এনভায়রনমেন্ট কপি করো (পুরো সোর্স কোড নয়)
COPY --from=builder /app/.venv /app/.venv
COPY backend/ .
# বাংলা মন্তব্য: রুট-লেভেল 'skills' ডিরেক্টরি কপি করা হচ্ছে যাতে
# core/evolution/auto_skill_creator.py সঠিকভাবে 'skills.installer' ইম্পোর্ট করতে পারে।
COPY skills/ ./skills/
# বাংলা মন্তব্য: রুট-লেভেলের ask_scribe.py কপি করা হলো যাতে api/routes/knowledge.py সফলভাবে এটি ইম্পোর্ট করতে পারে।
COPY ask_scribe.py ./

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# CRITICAL FIX (Cloud Run Port Binding):
# Always use shell form for CMD (e.g., `CMD uvicorn ...`) instead of JSON array (`CMD ["uvicorn", ...]`).
# The shell form allows Cloud Run to dynamically inject the $PORT environment variable.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
