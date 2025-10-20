#!/bin/bash
set -e

echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 15

# Pull model
echo "Checking for model..."
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "Pulling llama3.1:8b model (this may take 5-10 minutes)..."
    ollama pull llama3.1:8b
else
    echo "Model already exists"
fi

# Generate vector database
if [ ! -d "chroma_db" ]; then
    echo "Generating vector database..."
    python prepare_data.py
else
    echo "Vector database already exists"
fi

# Start FastAPI server
echo "Starting FastAPI server on port 8000..."
exec python server.py
```

### 5. **`.railwayignore`** (new file - optional but helpful):
```
.git
.gitignore
__pycache__
*.pyc
.vscode
.idea
.DS_Store
README.md
venv
env