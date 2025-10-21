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

echo "✅ Ollama is ready! Pulling 'phi' model if not already present..."

# 3. Pull the phi model (only downloads if not cached)
# This runs at startup instead of build time to avoid build timeouts
ollama pull phi

echo "✅ Model ready! Pre-warming with test request..."

# 4. Pre-warm the model with a minimal request (faster than full generation)
# Using a very short prompt and low token limit to speed up warm-up
# We add a 60-second timeout and '|| true' so that 'set -e'
# does NOT kill the script if the pre-warming fails.
# The server will start anyway, and the first API request will just be slow.
curl -X POST http://localhost:11434/api/generate \
     -H "Content-Type: application/json" \
     --max-time 60 \
     -d '{ "model": "phi", "prompt": "hi", "stream": false, "options": {"num_predict": 5} }' || true

echo "✅ Model pre-warm attempt complete! Starting server..."

# 4. Start FastAPI server (it will take over)
echo "🚀 Starting FastAPI server on port ${PORT:-8080}..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}