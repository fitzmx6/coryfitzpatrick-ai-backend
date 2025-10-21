#!/bin/bash
set -e

echo "=== Starting Services ==="

# 1. Start Ollama service in the background
echo "Starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &

# 2. Wait for Ollama to be FULLY ready
echo "Waiting for Ollama to initialize..."
max_attempts=60 # Wait for up to 60 seconds
attempt=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: Ollama failed to start after 60 seconds."
        echo "--- Ollama Log Dump ---"
        cat /tmp/ollama.log
        echo "-----------------------"
        exit 1
    fi
    echo "Waiting for Ollama... (Attempt $attempt/$max_attempts)"
    sleep 1
done

echo "✅ Ollama is ready! Pre-warming 'phi' model..."

# 3. Pre-warm the model by sending a dummy request
# This forces Ollama to load the model into RAM before Uvicorn starts.
# This will make the startup slower, but the first API request fast.
curl -s http://localhost:11434/api/generate \
  -d '{
        "model": "phi",
        "prompt": "hello",
        "stream": false
      }' > /dev/null

echo "✅ Model is pre-warmed!"

# 4. Start FastAPI server (it will take over)
echo "🚀 Starting FastAPI server on port ${PORT:-8080}..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}