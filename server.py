# server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import os
from contextlib import asynccontextmanager

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
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup:
    await load_models(app)
    yield
    # On shutdown:
    await close_models(app)

# Pass the lifespan manager to your FastAPI app
app = FastAPI(lifespan=lifespan)

# --- End Model Loading ---

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str

# --- Core Functions ---

def query_ollama(prompt: str) -> str:
    """Send prompt to local Ollama instance"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'phi',  # <-- CORRECTED: Was 'phi'
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.3,
                    'top_p': 0.9,
                }
            },
            timeout=120
        )
        response.raise_for_status() # Raise an error for bad responses (4xx, 5xx)
        return response.json()['response']
    except requests.RequestException as e:
        print(f"Ollama request failed: {e}")
        return "Sorry, I'm having trouble connecting to the AI model right now."


def get_relevant_context(request: Request, query: str, n_results: int = 5) -> str:
    """Search vector database for relevant information"""
    
    # Get models from app.state
    embedding_model = request.app.state.embedding_model
    collection = request.app.state.collection
    
    query_embedding = embedding_model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    if not results['documents'][0]:
        return ""
    
    context_parts = []
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        # Using 'answer' as the primary context, as 'question' is in metadata
        context_parts.append(f"Q: {metadata.get('question', '')}\nA: {metadata.get('answer', doc)}")
    
    return "\n\n".join(context_parts)

# --- API Endpoints ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(fastapi_request: Request, chat_request: ChatRequest):
    try:
        context = get_relevant_context(fastapi_request, chat_request.message, n_results=5)
        
        if not context:
            return ChatResponse(
                response="I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. Please ask about his background, technical expertise, or leadership experience."
            )
        
        system_prompt = """You are an AI assistant for Cory Fitzpatrick's professional portfolio. Your purpose is to help employers learn about Cory's qualifications for Software Engineering Manager and Tech Lead positions.

CRITICAL RULES:
1. ONLY answer questions about Cory's professional background, skills, experience, and achievements.
2. ONLY use information from the CONTEXT provided below.
3. If the question cannot be answered from the CONTEXT, say: "I don't have that specific information in Cory's profile. Please ask about his technical skills, leadership experience, projects, or achievements."
4. Never make up information.
5. Be professional and concise.

CONTEXT FROM CORY'S PROFILE:
{context}

USER QUESTION: {question}

Provide a helpful, accurate answer based ONLY on the context above:"""

        prompt = system_prompt.format(
            context=context,
            question=chat_request.message
        )
        
        response = query_ollama(prompt)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Error in /api/chat: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/health")
async def health():
    # This will now respond instantly
    return {"status": "healthy", "model": "phi"} # <-- CORRECTED: Was 'phi'


# --- ADD THIS BLOCK TO RUN THE SERVER ---
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable, default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting server locally on port {port}...")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)