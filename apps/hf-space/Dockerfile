# SupremeAI HuggingFace Space — Hybrid 8B Model Server
# Uses llama-cpp-python for GGUF inference
# বাংলা মন্তব্য: Text Generation Inference (TGI)-এর পরিবর্তে llama-cpp-python ও FastAPI ব্যবহার করে কাস্টম পাইথন সার্ভার রান করা হচ্ছে।
# সিকিউরিটি সুরক্ষার জন্য non-root appuser তৈরি করা হয়েছে।

# Use a clean Python base image instead of conflicting TGI
FROM python:3.10-slim

# Set environment variables for memory and unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/models/supreme-hybrid-8b-q4.gguf

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir llama-cpp-python fastapi uvicorn loguru structlog

# Create a non-root user for security hardening
RUN useradd -m -u 1000 appuser

# Copy model and application code
COPY supreme-hybrid-8b-q4.gguf /models/
COPY server.py /app/

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 80

# Run the custom server
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "80"]
