# server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import os
from contextlib import asynccontextmanager  # <-- Import this

# --- Model Loading with Lifespan ---

# This function runs when the app starts
async def load_models(app: FastAPI):
    print("Loading embedding model...")
    app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Connecting to ChromaDB...")
    app.state.chroma_client = chromadb.PersistentClient(path="./chroma_db")
    app.state.collection = app.state.chroma_client.get_collection("cory_profile")
    print("✅ Models and DB loaded!")

# This function runs when the app shuts down
async def close_models(app: FastAPI):
    print("Closing resources...")
    # You can add cleanup code here if needed
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    await load_models(app)
    yield
    # On shutdown
    await close_models(app)

# Pass the lifespan manager to your FastAPI app
app = FastAPI(lifespan=lifespan)

# --- End Model Loading ---

# Enable CORS for your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (keep your BaseModel classes ChatRequest and ChatResponse)
class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str
# ...

# --- Update your functions ---

def query_ollama(prompt: str) -> str:
    # ... (this function is fine, no change needed)
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'llama3.2',
            'prompt': prompt,
            'stream': False,
            'options': { 'temperature': 0.3, 'top_p': 0.9 }
        },
        timeout=120
    )
    return response.json()['response']

# Update this function to get models from app.state
def get_relevant_context(request: Request, query: str, n_results: int = 5) -> str:
    """Search vector database for relevant information"""
    
    # Get models from app.state instead of global scope
    embedding_model = request.app.state.embedding_model
    collection = request.app.state.collection
    
    # Generate embedding for the query
    query_embedding = embedding_model.encode([query]).tolist()
    
    # Search ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # ... (rest of this function is fine)
    if not results['documents'][0]:
        return ""
    
    context_parts = []
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        context_parts.append(f"Q: {metadata['question']}\nA: {metadata['answer']}")
    
    return "\n\n".join(context_parts)

# Update your endpoint to accept the 'Request' object
@app.post("/api/chat", response_model=ChatResponse)
async def chat(fastapi_request: Request, chat_request: ChatRequest):
    try:
        # Get relevant context from vector database
        # Pass the 'fastapi_request' to your context function
        context = get_relevant_context(fastapi_request, chat_request.message, n_results=5)
        
        if not context:
            return ChatResponse(
                response="I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. Please ask about his background, technical expertise, or leadership experience."
            )
        
        # ... (rest of your /api/chat endpoint is fine)
        
        # Build prompt for Ollama
        system_prompt = """You are an AI assistant for Cory Fitzpatrick's professional portfolio. Your purpose is to help employers and recruiters learn about Cory's qualifications for Software Engineering Manager and Tech Lead positions.

CRITICAL RULES:
1. ONLY answer questions about Cory's professional background, skills, experience, and achievements
2. ONLY use information from the CONTEXT provided below
3. If the question cannot be answered from the CONTEXT, say: "I don't have that specific information in Cory's profile. Please ask about his technical skills, leadership experience, projects, or achievements."
4. Never make up information or speculate
5. Be professional, concise, and helpful
6. Focus on what makes Cory a strong candidate for engineering leadership roles

CONTEXT FROM CORY'S PROFILE:
{context}

USER QUESTION: {question}

Provide a helpful, accurate answer based ONLY on the context above:"""

        prompt = system_prompt.format(
            context=context,
            question=chat_request.message
        )
        
        # Get response from Ollama
        response = query_ollama(prompt)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    # This will now respond instantly
    return {"status": "healthy", "model": "llama3.2"}

# ... (remove the __main__ block, it's not needed for uvicorn)