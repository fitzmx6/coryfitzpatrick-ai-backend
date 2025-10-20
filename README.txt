# Cory Fitzpatrick AI Portfolio Chatbot

This is the backend server for an AI-powered chatbot designed to answer questions about Cory Fitzpatrick's professional experience. It serves as an interactive, AI-driven resume and portfolio.

It’s built using a **Retrieval-Augmented Generation (RAG)** pipeline:

- **Web Server:** FastAPI (Python)  
- **LLM (Local):** Ollama running the `phi` model  
- **Vector Database:** ChromaDB  
- **Embedding Model:** `all-MiniLM-L6-v2`  
- **Deployment:** Railway (via `nixpacks.toml`)

---

## 🚀 Local Development Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/fitzmx6/coryfitzpatrick-ai-backend.git
cd coryfitzpatrick-ai-backend
```

---

### Step 2: Create and Activate Python Virtual Environment

#### On Mac/Linux
```bash
# Create virtual environment
python3 -m venv venv

# Activate it (you'll need to do this every time you work on the project)
source venv/bin/activate
```

#### On Windows
```bash
# Create virtual environment
python -m venv venv

# Activate it (you'll need to do this every time you work on the project)
venv\Scripts\activate
```

✅ **Success:** If you see `(venv)` in your terminal prompt, the virtual environment is active!

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

#### Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Corys experience at J&J?"}'
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

- **nixpacks.toml:** Configures the build step, installs Python, Ollama, and dependencies, and pre-pulls the `phi` model.  
- **start.sh:** Launches Ollama in the background and then starts the Uvicorn FastAPI server.  
- **Port:** Uses `$PORT` (default Railway 8080, local default 8000).

> ⚙️ You don’t need `nixpacks.toml` or `start.sh` for local development—only for production deployment.

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
