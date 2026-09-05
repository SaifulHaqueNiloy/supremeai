FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Create and switch to non-root user for security compliance (Trap #97)
RUN addgroup --system supremeai && adduser --system supremeai --ingroup supremeai && \
    chown -R supremeai:supremeai /app
USER supremeai

CMD ["python", "main.py"]
