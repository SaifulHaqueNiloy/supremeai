# SupremeAI HuggingFace Space — Hybrid 8B Model Server
# Uses llama-cpp-python for GGUF inference

FROM python:3.10-slim

# Prevent memory leaks and byte-code generation
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Copy the quantized model
COPY supreme-hybrid-8b-q4.gguf /models/supreme-hybrid-8b-q4.gguf

# Environment configuration
ENV MODEL_ID=/models/supreme-hybrid-8b-q4.gguf
ENV MAX_INPUT_LENGTH=4096
ENV MAX_TOTAL_TOKENS=8192
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Install Python dependencies for the inference server
RUN pip install --no-cache-dir llama-cpp-python huggingface-hub transformers torch fastapi uvicorn loguru pydantic

# Copy the inference server script
COPY server.py /app/server.py

# Switch to the non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]
