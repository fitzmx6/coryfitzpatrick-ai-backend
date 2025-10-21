# Cory Fitzpatrick AI Portfolio Chatbot

This is the backend server for an AI-powered chatbot designed to answer questions about Cory Fitzpatrick's professional experience. It serves as an interactive, AI-driven resume and portfolio.

It's built using a **Retrieval-Augmented Generation (RAG)** pipeline with **production optimizations**:

- **Web Server:** FastAPI (Python 3.11+)
- **LLM (Local):** Ollama running the `phi` model
- **Vector Database:** ChromaDB
- **Embedding Model:** `all-MiniLM-L6-v2`
- **Caching:** Redis (optional, with in-memory fallback)
- **Rate Limiting:** 20 requests/minute per IP
- **Compression:** GZIP for 70% smaller responses
- **Streaming:** Fast response streaming for better UX
- **Deployment:** Railway (via `nixpacks.toml`)

**Performance:** 85-95% faster responses with streaming + caching

---

## 🚀 Local Development Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/fitzmx6/coryfitzpatrick-ai-backend.git
cd coryfitzpatrick-ai-backend
```

---

### Step 2: Create and Activate Python Virtual Environment

**IMPORTANT:** This project requires **Python 3.11+** (uses modern type hints)

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

### Step 3: Install Dependencies
```bash
# Make sure you're in the venv (you should see (venv) in your prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Install and Start Ollama

1. Download and run the installer from [https://ollama.com/download](https://ollama.com/download).  
2. Ollama runs automatically as a service.

---

### Step 5: Download AI Model
```bash
# In a new terminal (keep ollama serve running)
ollama pull phi
```
💡 *The `phi` model is fast and efficient for CPU-based inference.*

---

### Step 6: Generate Vector Database
```bash
python prepare_data.py
```
✅ Expected output:  
`Successfully stored [X] documents in vector database!`

---

### Step 7: Start the Server
```bash
python server.py
```

Expected output:
```
Loading models...
✅ Models and DB loaded!
🚀 Starting server on port 8000
```

---

### Step 8: Test It

#### Test Health Endpoint
```bash
curl http://localhost:8000/health
```
Expected response:  
`{"status": "healthy", "model": "phi"}`

#### Test Chat Endpoint (Standard)
```bash
curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Corys experience at J&J?"}'
```

#### Test Streaming Endpoint (Recommended - Faster UX)
```bash
curl -X POST http://localhost:8000/api/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "What are Corys technical skills?"}' \
     --no-buffer
```

Or open in your browser:
👉 [http://localhost:8000/health](http://localhost:8000/health)

---

## 🔄 Daily Development Workflow

Every time you work on the project:
```bash
# 1. Navigate to project
cd coryfitzpatrick-ai-backend

# 2. Activate virtual environment
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Make sure Ollama is running (in another terminal)
ollama serve

# 4. Start the server
python server.py

# 5. When done, deactivate venv
deactivate
```

---

## 🚢 Deployment (Railway)

This project is configured for deployment on **Railway** using **Nixpacks**.

**For complete deployment instructions, see:** [DEPLOYMENT.md](DEPLOYMENT.md)

### Quick Deploy Overview:
1. Push code to GitHub
2. Create Railway project from GitHub repo
3. **Add Redis plugin** (optional but recommended for caching)
4. Generate domain
5. Test endpoints

### Key Files:
- **nixpacks.toml:** Configures build (Python 3.11, Ollama, dependencies)
- **start.sh:** Launches Ollama and FastAPI server
- **railway.json:** Health check and restart policy

### Optimizations Included:
✅ Streaming responses (2-3s perceived time)
✅ Redis caching (99%+ faster repeat queries)
✅ GZIP compression (70% smaller transfers)
✅ Rate limiting (20 req/min protection)
✅ Vector search filtering (better quality)
✅ Fast cold starts (~30s)

> ⚙️ You don't need `nixpacks.toml` or `start.sh` for local development—only for production deployment.

---

## 📚 Documentation

Comprehensive guides for optimization and deployment:

| Guide | Purpose |
|-------|---------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Complete Railway deployment walkthrough |
| **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** | Performance tuning and configuration |
| **[TESTING.md](TESTING.md)** | Local and production testing procedures |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Fast lookup for settings and commands |
| **[OPTIMIZATIONS_SUMMARY.md](OPTIMIZATIONS_SUMMARY.md)** | Overview of all improvements |

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
python server.py
```

---

## 🧠 Summary

This project demonstrates how to build a personal AI-driven portfolio using a RAG pipeline.  
It blends **local inference (Ollama)**, **semantic retrieval (ChromaDB)**, and **FastAPI** for a fast, private, and interactive experience.  

Built with ❤️ by **Cory Fitzpatrick**  
[www.coryfitzpatrick.com](http://www.coryfitzpatrick.com)
