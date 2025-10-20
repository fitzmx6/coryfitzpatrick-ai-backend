## 🚀 Local Development Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/fitzmx6/coryfitzpatrick-ai-backend.git
cd coryfitzpatrick-ai-backend
```

### Step 2: Create and Activate Python Virtual Environment

**On Mac/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it (you'll need to do this every time you work on the project)
source venv/bin/activate

# Your terminal prompt should now show (venv) at the beginning
```

**On Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate it (you'll need to do this every time you work on the project)
venv\Scripts\activate

# Your terminal prompt should now show (venv) at the beginning
```

**✅ Success**: If you see `(venv)` in your terminal, you're in the virtual environment!

### Step 3: Install Dependencies
```bash
# Make sure you're in the venv (you should see (venv) in your prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install and Start Ollama

**On Mac:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama (in a separate terminal, or add & to run in background)
ollama serve
```

**On Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

**On Windows:**
```bash
# Download from https://ollama.com/download and run installer
# Ollama runs automatically as a service
```

### Step 5: Download AI Model
```bash
# In a new terminal (keep ollama serve running)
ollama pull llama3.1:3b

# Wait 3-5 minutes for download to complete
```

### Step 6: Generate Vector Database
```bash
# Back in your original terminal with (venv) active
python prepare_data.py

# You should see: ✅ Successfully stored 47 documents in vector database!
```

### Step 7: Start the Server
```bash
# Make sure (venv) is active and Ollama is running
python server.py

# You should see:
# Loading models...
# ✅ Models loaded!
# 🚀 Starting server on port 8000
```

### Step 8: Test It

**In a new terminal:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Corys experience at JJ?"}'
```

**Or open in browser:**
```
http://localhost:8000/health
```

---

## 🔄 Daily Development Workflow

**Every time you work on the project:**
```bash
# 1. Navigate to project
cd coryfitzpatrick-ai-backend

# 2. Activate virtual environment
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# 3. Make sure Ollama is running (check in another terminal)
ollama serve                      # If not already running

# 4. Start your server
python server.py

# 5. When done, deactivate venv
deactivate
```

---

## 💡 Quick Tips

**Check if venv is active:**
```bash
which python     # Mac/Linux - should show path to venv/bin/python
where python     # Windows - should show path to venv\Scripts\python
```

**If you see "command not found" for python:**
```bash
# Make sure venv is activated
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
```

**To exit the virtual environment:**
```bash
deactivate
```

**If you close your terminal and come back:**
```bash
cd coryfitzpatrick-ai-backend
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows
python server.py
```