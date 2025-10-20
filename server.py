# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json

app = FastAPI()

# Enable CORS for your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
print("Loading models...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection("cory_profile")
print("✅ Models loaded!")

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str

def query_ollama(prompt: str) -> str:
    """Send prompt to local Ollama instance"""
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'llama3.1:8b',
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.3,
                'top_p': 0.9,
            }
        },
        timeout=120
    )
    return response.json()['response']

def get_relevant_context(query: str, n_results: int = 5) -> str:
    """Search vector database for relevant information"""
    
    # Generate embedding for the query
    query_embedding = embedding_model.encode([query]).tolist()
    
    # Search ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # Format results
    if not results['documents'][0]:
        return ""
    
    context_parts = []
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        context_parts.append(f"Q: {metadata['question']}\nA: {metadata['answer']}")
    
    return "\n\n".join(context_parts)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get relevant context from vector database
        context = get_relevant_context(request.message, n_results=5)
        
        if not context:
            return ChatResponse(
                response="I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. Please ask about his background, technical expertise, or leadership experience."
            )
        
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
            question=request.message
        )
        
        # Get response from Ollama
        response = query_ollama(prompt)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting server on http://localhost:8000")
    print("📚 Make sure Ollama is running: ollama serve")
    uvicorn.run(app, host="0.0.0.0", port=8000)