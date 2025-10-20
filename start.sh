#!/bin/bash
set -e

echo "=== Starting Services ==="

# 1. Start Ollama service in the background
echo "Starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &

# 2. Wait for Ollama to be ready
echo "Waiting for Ollama to initialize..."
while ! curl -s http://localhost:11434/ > /dev/null 2>&1; do
   echo "Waiting for Ollama..."
   sleep 1
done
echo "✅ Ollama is ready!"

# 3. Start FastAPI server (using the port Railway provides)
echo "🚀 Starting FastAPI server on port ${PORT:-8080}..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}