# Cory Fitzpatrick AI Portfolio Chatbot

This is the backend server for an AI-powered chatbot designed to answer questions about Cory Fitzpatrick's professional experience. It serves as an interactive, AI-driven resume and portfolio.

It's built using a **Retrieval-Augmented Generation (RAG)** pipeline with **production optimizations**:

- **Web Server:** FastAPI (Python 3.11+)
- **LLM:** Groq API with Llama 3.1 8B Instant (ultra-fast, free)
- **Vector Database:** ChromaDB
- **Embedding Model:** `all-MiniLM-L6-v2`
- **Caching:** Redis (optional, with in-memory fallback)
- **Rate Limiting:** 20 requests/minute per IP
- **Compression:** GZIP for 70% smaller responses
- **Streaming:** Fast response streaming for better UX
- **Deployment:** Google Cloud Run (via Docker & Cloud Build)

**Performance:** Ultra-fast responses (<1s) with Groq + caching + streaming

---

## ⚡ TL;DR - Quick Start

Already have everything installed? Here are the essential commands:

```bash
# 1. Activate the python venv
source venv/bin/activate

# 2. Prepare the vector database (first time only)
cory-ai-prepare-data

# 3. Start the backend server (leave running)
cory-ai-server

# 4. In a new terminal, start the interactive chatbot
cory-ai-chatbot
```

**Alternative using Python module syntax:**
```bash

# 1. Activate the Python env
source venv/bin/activate

# 2. Prepare data
python -m cory_ai_chatbot.prepare_data

# 3. Start server
python -m cory_ai_chatbot.server

# 4. Start chatbot
python -m cory_ai_chatbot.cli
```

Need to set up from scratch? Continue to the full setup guide below.

---

## 🚀 Local Development Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/fitzmx6/coryfitzpatrick-ai-backend.git
cd coryfitzpatrick-ai-backend
```

---

### Step 2: Create and Activate Python Virtual Environment

**IMPORTANT:** This project requires **Python 3.11+**

#### On Mac/Linux
```bash
# Install Python 3.11 if needed
brew install python@3.11

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate it (you'll need to do this every time you work on the project)
source venv/bin/activate

# Verify version (should be 3.11+)
python --version
```

#### On Windows
```bash
# Download Python 3.11+ from python.org first

# Create virtual environment
python -m venv venv

# Activate it (you'll need to do this every time you work on the project)
venv\Scripts\activate

# Verify version (should be 3.11+)
python --version
```

✅ **Success:** If you see `(venv)` in your terminal prompt and Python 3.11+, you're ready!

---

### Step 3: Install the Package
```bash
# Make sure you're in the venv (you should see (venv) in your prompt)
pip install --upgrade pip

# Install in editable/development mode
pip install -e .

# Or for development with testing tools
pip install -e ".[dev]"
```

This installs the `cory-ai-chatbot` package and all dependencies.

---

### Step 4: Get a Free Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to "API Keys" and create a new key
4. Copy the API key

---

### Step 5: Set Environment Variable

#### Mac/Linux
```bash
export GROQ_API_KEY="your-api-key-here"
```

#### Windows (PowerShell)
```powershell
$env:GROQ_API_KEY="your-api-key-here"
```

💡 *For permanent setup, add to your ~/.bashrc or ~/.zshrc (Mac/Linux)*

---

### Step 6: Prepare Training Data (First Time Only)
```bash
# Run this once to create the vector database from training data
cory-ai-prepare-data
```

This will create the ChromaDB vector database in `data/chroma_db/`.

---

### Step 7: Start the FastAPI Server
```bash
# Option 1: Using the CLI command (recommended)
cory-ai-server

# Option 2: Using Python module
python -m cory_ai_chatbot.server
```

**Note:** This starts the **backend API server**. Leave this running in your terminal.

Expected output:
```
⏳ Loading embedding model...
✅ Embedding model loaded in 2.3s
⏳ Connecting to ChromaDB...
✅ ChromaDB connected in 0.5s
🚀 All models loaded! Total startup time: 2.8s
🚀 Starting server on port 8000
```

---

### Step 8: Test It

#### Interactive Chat Client (Best Way to Test)

**Important:** Make sure the server is running first (from Step 7). Then, in a **new terminal window**:

```bash
cory-ai-chatbot
```

This will start an interactive chat session where you can:
- Ask questions about Cory's experience and skills
- Have multi-turn conversations with context
- See streaming responses in real-time
- Type `quit` or `exit` to end the session

Example session:
```
You: What is Cory good at?
Cory's AI Assistant: Based on Cory's profile, he is good at...

You: How can I contact him?
Cory's AI Assistant: You can contact Cory via email at...

You: quit
Goodbye! Thanks for chatting!
```

---

#### Alternative: Test with curl Commands

#### Test Root Endpoint (Service Info)

**Local:**
```bash
curl http://localhost:8000/
```

**Production:**
```bash
curl https://your-cloud-run-service-url.run.app/
```

Expected response:
```json
{
  "service": "Cory Fitzpatrick AI Portfolio Chatbot",
  "status": "online",
  "endpoints": {
    "health": "/health",
    "chat": "/api/chat (POST)",
    "chat_stream": "/api/chat/stream (POST)"
  },
  "model": "llama-3.1-8b-instant",
  "provider": "groq"
}
```

#### Test Health Endpoint

**Local:**
```bash
curl http://localhost:8000/health
```

**Production:**
```bash
curl https://your-cloud-run-service-url.run.app/health
```

Expected response:
```json
{"status": "healthy", "model": "llama-3.1-8b-instant", "provider": "groq"}
```

#### Test Chat Endpoint (Standard)

**Local:**
```bash
curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Corys experience at J&J?"}'
```

**Production:**
```bash
curl -X POST https://your-cloud-run-service-url.run.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Corys experience at J&J?"}'
```

#### Test Streaming Endpoint (Recommended - Faster UX)

**Local:**
```bash
curl -X POST http://localhost:8000/api/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "What are Corys technical skills?"}' \
     --no-buffer
```

**Production:**
```bash
curl -X POST https://your-cloud-run-service-url.run.app/api/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "What are Corys technical skills?"}' \
     --no-buffer
```

**Test in your browser:**

Local:
- 👉 [http://localhost:8000/](http://localhost:8000/)
- 👉 [http://localhost:8000/health](http://localhost:8000/health)

Production:
- 👉 Replace with your Cloud Run service URL after deployment

---

## 🔄 Daily Development Workflow

Every time you work on the project:
```bash
# 1. Navigate to project
cd coryfitzpatrick-ai-backend

# 2. Activate virtual environment
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Set Groq API key (if not in your shell profile)
export GROQ_API_KEY="your-api-key-here"  # Mac/Linux
$env:GROQ_API_KEY="your-api-key-here"    # Windows

# 4. Start the server
cory-ai-server

# 5. When done, deactivate venv
deactivate
```

---

## 🚢 Deployment (Google Cloud Run)

This project is configured for deployment on **Google Cloud Run** using **Docker** and **Cloud Build**.

### Quick Deploy Overview:
1. Push code to GitHub
2. Set up Google Cloud Project and connect GitHub repository
3. Configure Cloud Build trigger using `cloudbuild.yaml`
4. Trigger deployment (automatic on push to main)
5. **Add Environment Variables** in Cloud Run Console:
   - `GROQ_API_KEY` (required - get from https://console.groq.com)
   - `SYSTEM_PROMPT` (required - full system prompt text)
6. Set Memory to **1 GiB** (required for ML model loading)
7. Test endpoints at your Cloud Run service URL

### Environment Variables:

**Required:**
- `GROQ_API_KEY` - Your Groq API key for LLM inference
- `SYSTEM_PROMPT` - Full system prompt text (from `system_prompt.txt`)

**Optional:**
- `REDIS_URL` - Redis connection string for caching (optional but recommended)
- `PORT` - Server port (Cloud Run auto-sets to 8080, defaults to 8000 locally)

### Key Files:
- **Dockerfile:** Configures Docker image with Python 3.11, dependencies, and pre-downloaded ML model
- **cloudbuild.yaml:** Cloud Build configuration with Docker layer caching for fast builds
- **.dockerignore:** Excludes unnecessary files from Docker builds

### Deployment Steps (Console):

1. **Initial Setup:**
   - Create a Google Cloud Project
   - Enable Cloud Run and Cloud Build APIs
   - Connect your GitHub repository

2. **Configure Cloud Build Trigger:**
   - Go to Cloud Build > Triggers
   - Edit your trigger configuration
   - Set **Build Configuration** to: `cloudbuild.yaml`
   - This enables Docker layer caching (2-3 min builds instead of 15 min)

3. **Deploy:**
   - Push to main branch (or manually trigger build)
   - Wait for build to complete (~15 min first time, ~2-3 min after)

4. **Configure Service:**
   - Go to Cloud Run > Your Service
   - Click **"EDIT & DEPLOY NEW REVISION"**
   - Add environment variables (see above)
   - Set **Memory** to 1 GiB
   - Click **"DEPLOY"**

### Optimizations Included:
✅ Ultra-fast responses with Groq (<1s)
✅ Streaming responses for better UX
✅ Docker layer caching for fast builds (2-3 min)
✅ Pre-downloaded ML model in Docker image (no HuggingFace rate limits)
✅ Redis caching support (99%+ faster repeat queries)
✅ GZIP compression (70% smaller transfers)
✅ Rate limiting (20 req/min protection)
✅ Vector search filtering (better quality)
✅ Fast cold starts (~2-3s)

### Cost Estimate:
With **300 API calls/month** on Cloud Run's free tier:
- Free tier: 2M requests/month, 360k GB-seconds/month
- Your usage: ~0.00001% of free tier = **$0.00/month**
- First 2M requests are free, then ~$0.40 per million

> ⚙️ You don't need `Dockerfile` or `cloudbuild.yaml` for local development—only for production deployment.

---

## 💡 Quick Tips

### Check if Virtual Environment is Active
```bash
which python      # Mac/Linux - should show path to venv/bin/python
where python      # Windows - should show path to venv\Scripts\python
```

### If Python Commands Fail
Make sure your virtual environment is activated:
```bash
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
```

### To Exit the Virtual Environment
```bash
deactivate
```

### If You Reopen Your Terminal
```bash
cd coryfitzpatrick-ai-backend
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
cory-ai-server
```

---

## 📁 Project Structure

```
cory-ai-chatbot/
├── src/
│   └── cory_ai_chatbot/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # FastAPI server
│       ├── cli.py               # Interactive chat client
│       └── prepare_data.py      # Vector database preparation
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_server.py           # Server unit tests
│   └── test_cli.py              # CLI unit tests
├── data/
│   ├── training_data.jsonl      # Training data
│   └── chroma_db/               # Vector database (generated)
├── docs/
│   └── testing.md               # Testing documentation
├── Dockerfile                   # Docker image configuration
├── cloudbuild.yaml              # Cloud Build configuration
├── .dockerignore                # Docker build exclusions
├── pyproject.toml               # Package configuration
├── pytest.ini                   # Pytest configuration
└── README.md                    # This file
```

### CLI Commands

After installation with `pip install -e .`, three commands are available:

- **`cory-ai-server`** - Start the FastAPI backend server (required for the chatbot to work)
- **`cory-ai-chatbot`** - Launch interactive chat client (requires server to be running)
- **`cory-ai-prepare-data`** - Create/update vector database from training data

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cory_ai_chatbot

# Run specific test file
pytest tests/test_server.py

# Run with verbose output
pytest -v
```

---

## 🧠 Summary

This project demonstrates how to build a personal AI-driven portfolio using a RAG pipeline.
It blends **cloud-based LLM inference (Groq)**, **semantic retrieval (ChromaDB)**, and **FastAPI** for ultra-fast, production-ready responses.

Built by **Cory Fitzpatrick**
[www.coryfitzpatrick.com](http://www.coryfitzpatrick.com)
