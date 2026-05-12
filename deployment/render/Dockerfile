FROM ollama/ollama:latest

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set Ollama to listen on all interfaces (default port 11434)
ENV OLLAMA_HOST=0.0.0.0

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Start using the script
ENTRYPOINT ["/bin/bash", "/start.sh"]
