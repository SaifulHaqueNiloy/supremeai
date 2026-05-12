#!/bin/bash
# start.sh - Pull model and start Ollama

# Start Ollama in the background
ollama serve &

# Wait for Ollama to start
echo "Waiting for Ollama to start on $OLLAMA_HOST..."
# Extract port from OLLAMA_HOST or default to 11434
PORT=$(echo $OLLAMA_HOST | cut -d: -f2)
if [ -z "$PORT" ] || [ "$PORT" == "$OLLAMA_HOST" ]; then
  PORT=11434
fi

until curl -s http://localhost:$PORT/api/tags > /dev/null; do
  sleep 2
done

# Pull the model specified by MODEL_NAME
if [ -n "$MODEL_NAME" ]; then
  echo "🚀 Pulling model: $MODEL_NAME"
  ollama pull $MODEL_NAME
  echo "✅ Model $MODEL_NAME pulled successfully."
else
  echo "⚠️ No MODEL_NAME specified, skipping pull."
fi

# Keep the process alive
wait
