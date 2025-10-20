#!/bin/bash
set -e

echo "=== Starting Cory AI Chatbot (3B Model) ==="

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to initialize..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: Ollama failed to start"
        cat /tmp/ollama.log
        exit 1
    fi
    echo "Attempt $attempt/$max_attempts - waiting for Ollama..."
    sleep 2
done

echo "✅ Ollama is ready!"

# Check if model exists, download if needed
echo "Checking for llama3.2 model..."
if ! ollama list | grep -q "llama3.2"; then
    echo "Downloading llama3.2 model (~2GB - this will take 3-5 minutes on first start)..."
    ollama pull llama3.2 || {
        echo "ERROR: Failed to download model"
        exit 1
    }
    echo "✅ Model downloaded successfully!"
else
    echo "✅ Model already exists"
fi

# Generate vector database if needed
if [ ! -d "chroma_db" ]; then
    echo "Generating vector database from training data..."
    python prepare_data.py || {
        echo "ERROR: Failed to generate vector database"
        exit 1
    }
    echo "✅ Vector database created!"
else
    echo "✅ Vector database already exists"
fi

# Start FastAPI server
echo "🚀 Starting FastAPI server on port ${PORT:-8000}..."
echo "Model: llama3.2 (2GB, optimized for speed and efficiency)"
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}