# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime — browser-ready image (Playwright + Chromium)
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Bengali comment (DEP-AUDIT): Chromium only lives in this image.
# Base OS utilities first (playwright's --with-deps runs its own apt-get later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder (brings in the playwright CLI)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Install Chromium + OS-level browser deps. MUST run AFTER the playwright
# package is copied above — otherwise the `playwright` CLI does not exist
# yet and the image build fails.
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create and use non-root user for security compliance
RUN addgroup --system supremeai && adduser --system supremeai --ingroup supremeai \
    && chown -R supremeai:supremeai /app

USER supremeai

# Expose port
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]