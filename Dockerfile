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
# বাংলা মন্তব্য: Render free tier-এ 'tools' group (playwright, pandas, matplotlib ~500MB) বাদ দেওয়া হয়েছে।
# শুধু 'main' group install করা হবে — এতে build দ্রুত হবে এবং memory limit exceed হবে না।
RUN poetry install --no-interaction --no-ansi --no-root --only main


# Stage 2: Runner
FROM python:3.11-slim AS runner
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

# শুধুমাত্র ভার্চুয়াল এনভায়রনমেন্ট কপি করো (পুরো সোর্স কোড নয়)
COPY --from=builder /app/.venv /app/.venv
COPY backend/ .
# বাংলা মন্তব্য: রুট-লেভেল 'skills' ডিরেক্টরি কপি করা হচ্ছে যাতে
# core/evolution/auto_skill_creator.py সঠিকভাবে 'skills.installer' ইম্পোর্ট করতে পারে।
COPY skills/ ./skills/
# বাংলা মন্তব্য: রুট-লেভেলের ask_scribe.py কপি করা হলো যাতে api/routes/knowledge.py সফলভাবে এটি ইম্পোর্ট করতে পারে।
COPY ask_scribe.py ./


ENV PATH="/app/.venv/bin:$PATH"
# বাংলা: EXPOSE port, CMD-এর ${PORT:-8080} default-এর সাথে consistent
EXPOSE 8080

# CRITICAL FIX (Cloud Run Port Binding):
# Always use shell form for CMD (e.g., `CMD uvicorn ...`) instead of JSON array (`CMD ["uvicorn", ...]`).
# The shell form allows Cloud Run to dynamically inject the $PORT environment variable.
# বাংলা মন্তব্য: আগে এখানে deprecated GUNICORN_WORKERS (ডিফল্ট 4) পড়া হতো — main.py-তে
# UVICORN_WORKERS=1 ডিফল্ট করে OOM ফিক্স করার চেষ্টা হলেও, প্রোডাকশনে আসল entrypoint এই
# Dockerfile CMD-ই (main.py-র প্রোগ্রাম্যাটিক uvicorn.run() নয়), তাই সেই ফিক্স কখনো কার্যকর
# হয়নি — Render free tier-এর 512MB RAM-এ 4টা worker লোড হয়ে OOM crash ঘটাতে পারত।
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers ${UVICORN_WORKERS:-1}"]
