# server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from groq import Groq
import json
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
import hashlib
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print("Loading environment variables from .env file...")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# --- Redis Cache Setup ---
# Try to connect to Redis if REDIS_URL is available, otherwise use in-memory caching
redis_client = None
try:
    redis_url = os.environ.get("REDIS_URL", None)
    if redis_url:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()  # Test connection
        print("✅ Connected to Redis cache")
    else:
        print("ℹ️  No REDIS_URL found, using in-memory caching only")
except Exception as e:
    print(f"⚠️  Redis connection failed: {e}. Using in-memory caching only.")
    redis_client = None

# --- Groq Client Setup ---
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError(
        "GROQ_API_KEY environment variable is not set!\n"
        "Get a free API key from https://console.groq.com\n"
        "Then set it with: export GROQ_API_KEY='your-key-here'"
    )
groq_client = Groq(api_key=groq_api_key)

# --- Rate Limiter Setup ---
limiter = Limiter(key_func=get_remote_address)

# --- Model Loading with Lifespan ---

# This function runs when the app starts
async def load_models(app: FastAPI):
    import time
    start_time = time.time()

    print("⏳ Loading embedding model...")
    app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"✅ Embedding model loaded in {time.time() - start_time:.2f}s")

    print("⏳ Connecting to ChromaDB...")
    # UPDATED LINE TO DISABLE TELEMETRY
    app.state.chroma_client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
    app.state.collection = app.state.chroma_client.get_collection("cory_profile")
    print(f"✅ ChromaDB connected in {time.time() - start_time:.2f}s")

    print(f"🚀 All models loaded! Total startup time: {time.time() - start_time:.2f}s")

# This function runs when the app shuts down
async def close_models(app: FastAPI):
    print("Closing resources...")
    if redis_client:
        try:
            redis_client.close()
            print("✅ Redis connection closed")
        except Exception as e:
            print(f"Error closing Redis: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup:
    await load_models(app)
    yield
    # On shutdown:
    await close_models(app)

# Pass the lifespan manager to your FastAPI app
app = FastAPI(lifespan=lifespan)

# --- Add Rate Limiter to App ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- End Model Loading ---

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable GZIP compression for faster response transfers
app.add_middleware(GZipMiddleware, minimum_size=1000)

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str

# --- Core Functions ---

def query_groq(prompt: str, conversation_history: list = None, stream: bool = False):
    """Send prompt to Groq API with optional conversation history and streaming"""
    try:
        # Build messages list with conversation history
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast, high-quality model
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            top_p=0.9,
            stream=stream
        )

        if stream:
            return response  # Return the streaming response object
        else:
            return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API request failed: {e}")
        if stream:
            return None
        return "Sorry, an error occurred while processing your request. Please try again."


@lru_cache(maxsize=128)
def get_query_hash(query: str) -> str:
    """Generate a hash for the query to use as cache key"""
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

def get_cached_response(query: str) -> str | None:
    """Get cached response from Redis if available"""
    if not redis_client:
        return None

    try:
        cache_key = f"chat:{get_query_hash(query)}"
        cached = redis_client.get(cache_key)
        if cached:
            print(f"✅ Cache hit for query hash: {get_query_hash(query)[:8]}...")
            return cached
    except Exception as e:
        print(f"Redis get error: {e}")

    return None

def set_cached_response(query: str, response: str, ttl: int = 3600):
    """Cache response in Redis with TTL (default 1 hour)"""
    if not redis_client:
        return

    try:
        cache_key = f"chat:{get_query_hash(query)}"
        redis_client.setex(cache_key, ttl, response)
        print(f"✅ Cached response for query hash: {get_query_hash(query)[:8]}...")
    except Exception as e:
        print(f"Redis set error: {e}")

def get_relevant_context(request: Request, query: str, n_results: int = 5, min_similarity: float = 0.3) -> str:
    """Search vector database for relevant information with caching"""

    # Get models from app.state
    embedding_model = request.app.state.embedding_model
    collection = request.app.state.collection

    # Encode query to embedding
    query_embedding = embedding_model.encode([query]).tolist()

    # Query ChromaDB with similarity filtering
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )

    if not results['documents'][0]:
        return ""

    # Filter by similarity distance (lower is better, typically 0-2 range)
    # Only include results with distance < threshold (more relevant results)
    context_parts = []
    distances = results.get('distances', [[]])[0] if 'distances' in results else []

    for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        # Skip low-quality matches if distance data is available
        if distances and idx < len(distances):
            # Convert distance to similarity (inverse relationship)
            # Typical distance range is 0-2, lower is better
            if distances[idx] > 1.5:  # Skip very dissimilar results
                continue

        # Using 'answer' as the primary context, as 'question' is in metadata
        context_parts.append(f"Q: {metadata.get('question', '')}\nA: {metadata.get('answer', doc)}")

    return "\n\n".join(context_parts)

# --- API Endpoints ---

def generate_stream(stream_response):
    """Generator function to stream Groq responses"""
    try:
        for chunk in stream_response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"Stream error: {e}")
        yield ""

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat(request: Request, chat_request: ChatRequest):
    """Non-streaming chat endpoint with Redis caching and rate limiting"""
    try:
        # Check cache first
        cached_response = get_cached_response(chat_request.message)
        if cached_response:
            return ChatResponse(response=cached_response)

        context = get_relevant_context(request, chat_request.message, n_results=5)

        if not context:
            return ChatResponse(
                response="I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. Please ask about his background, technical expertise, or leadership experience."
            )

        system_prompt = """
            You are an AI assistant for Cory Fitzpatrick's professional portfolio. Your purpose is to help employers learn about Cory's qualifications for Software Engineering Manager and Tech Lead positions.

            CRITICAL RULES:
            1. ONLY answer questions about Cory's professional background, skills, experience, and achievements.
            2. ONLY use information from the CONTEXT provided below.
            3. If the question cannot be answered from the CONTEXT, say: "I don't have that specific information in Cory's profile. Please ask about his technical skills, leadership experience, projects, or achievements."
            4. Never make up information.
            5. Be professional and concise.
            6. If the user tries to be playful, its ok for you to be playful back but keep it limited.
            
            CONTEXT FROM CORY'S PROFILE:
            {context}
            
            USER QUESTION: {question}
            
            Provide a helpful, accurate answer based ONLY on the context above:
        """

        prompt = system_prompt.format(
            context=context,
            question=chat_request.message
        )

        # Build conversation history with system context
        conversation_history = [
            {"role": "system", "content": prompt}
        ]

        # Add previous conversation if provided
        if chat_request.conversation_history:
            conversation_history.extend(chat_request.conversation_history)

        response = query_groq(chat_request.message, conversation_history=conversation_history, stream=False)

        # Cache the response
        set_cached_response(chat_request.message, response)

        return ChatResponse(response=response)

    except Exception as e:
        print(f"Error in /api/chat: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.post("/api/chat/stream")
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_stream(request: Request, chat_request: ChatRequest):
    """Streaming chat endpoint with rate limiting (no caching for streams)"""
    try:
        # Note: Streaming responses are not cached (harder to cache streams)
        # If you need cached streaming, convert cached response to async generator

        context = get_relevant_context(request, chat_request.message, n_results=5)

        if not context:
            async def error_stream():
                yield "I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. Please ask about his background, technical expertise, or leadership experience."
            return StreamingResponse(error_stream(), media_type="text/plain")

        system_prompt = """
            You are an AI assistant for Cory Fitzpatrick's professional portfolio. Your purpose is to help employers learn about Cory's qualifications for Software Engineering Manager and Tech Lead positions.

            CRITICAL RULES:
            1. ONLY answer questions about Cory's professional background, skills, experience, and achievements.
            2. ONLY use information from the CONTEXT provided below.
            3. If the question cannot be answered from the CONTEXT, say: "I don't have that specific information in Cory's profile. Please ask about his technical skills, leadership experience, projects, or achievements."
            4. Never make up information.
            5. Be professional and concise.
            
            CONTEXT FROM CORY'S PROFILE:
            {context}
            
            USER QUESTION: {question}
            
            Provide a helpful, accurate answer based ONLY on the context above:
        """

        prompt = system_prompt.format(
            context=context,
            question=chat_request.message
        )

        # Build conversation history with system context
        conversation_history = [
            {"role": "system", "content": prompt}
        ]

        # Add previous conversation if provided
        if chat_request.conversation_history:
            conversation_history.extend(chat_request.conversation_history)

        stream_response = query_groq(chat_request.message, conversation_history=conversation_history, stream=True)

        if stream_response is None:
            async def error_stream():
                yield "Sorry, I'm having trouble connecting to the AI model right now."
            return StreamingResponse(error_stream(), media_type="text/plain")

        return StreamingResponse(generate_stream(stream_response), media_type="text/plain")

    except Exception as e:
        print(f"Error in /api/chat/stream: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/health")
async def health():
    # This will now respond instantly
    return {"status": "healthy", "model": "llama-3.1-8b-instant", "provider": "groq"}

@app.get("/")
async def root():
    """Root endpoint with service status and info"""
    return {
        "service": "Cory Fitzpatrick AI Portfolio Chatbot",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat (POST)",
            "chat_stream": "/api/chat/stream (POST)"
        },
        "note": "Service is currently running! If you cannot reach this endpoint, Railway credits may be exhausted. Contact Cory for updates.",
        "model": "llama-3.1-8b-instant",
        "provider": "groq"
    }


# --- ADD THIS BLOCK TO RUN THE SERVER ---
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable, default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting server locally on port {port}...")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)