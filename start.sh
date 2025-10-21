#!/bin/bash
set -e

echo "=== Starting Cory Fitzpatrick AI Chatbot ==="

# Start FastAPI server
echo "🚀 Starting FastAPI server on port ${PORT:-8080}..."
exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}