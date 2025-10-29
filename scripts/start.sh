#!/bin/bash
set -e

echo "=== Starting Cory Fitzpatrick AI Chatbot ==="

# Generate vector database from training data
echo "📊 Generating vector database..."
cory-ai-prepare-data

# Start FastAPI server
echo "🚀 Starting FastAPI server on port ${PORT:-8080}..."
exec uvicorn cory_ai_chatbot.server:app --host 0.0.0.0 --port ${PORT:-8080}