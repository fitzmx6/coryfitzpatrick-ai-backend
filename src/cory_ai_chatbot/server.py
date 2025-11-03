# server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
import hashlib
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Determine the project root (three levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ============================================================================
# Configuration Constants
# ============================================================================

# Model Configuration
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
LLM_MODEL_NAME = "llama-3.1-8b-instant"
COLLECTION_NAME = "cory_profile"

# Vector Search Configuration
N_SEARCH_RESULTS = 5
MAX_DISTANCE_THRESHOLD = 1.5  # Maximum cosine distance for relevant results

# Cache Configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds

# LLM Generation Parameters
GROQ_TEMPERATURE = 0.3
GROQ_MAX_TOKENS = 500
GROQ_TOP_P = 0.9

# Load environment variables from .env file if it exists
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    print("Loading environment variables from .env file...")
    load_dotenv(env_file, verbose=False)  # Suppress parsing warnings

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
async def load_models(fastapi_app: FastAPI):
    import time
    start_time = time.time()

    print("⏳ Loading embedding model...")
    # noinspection PyUnresolvedReferences
    fastapi_app.state.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"✅ Embedding model loaded in {time.time() - start_time:.2f}s")

    print("⏳ Connecting to ChromaDB...")
    chroma_path = DATA_DIR / "chroma_db"
    # noinspection PyUnresolvedReferences
    fastapi_app.state.chroma_client = chromadb.PersistentClient(path=str(chroma_path), settings=Settings(anonymized_telemetry=False))
    # noinspection PyUnresolvedReferences
    fastapi_app.state.collection = fastapi_app.state.chroma_client.get_collection(COLLECTION_NAME)
    print(f"✅ ChromaDB connected in {time.time() - start_time:.2f}s")

    print(f"🚀 All models loaded! Total startup time: {time.time() - start_time:.2f}s")

# This function runs when the app shuts down
async def close_models(fastapi_app: FastAPI):
    print("Closing resources...")
    if redis_client:
        try:
            redis_client.close()
            print("✅ Redis connection closed")
        except Exception as redis_close_error:
            print(f"Error closing Redis: {redis_close_error}")

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # On startup:
    await load_models(fastapi_app)
    yield
    # On shutdown:
    await close_models(fastapi_app)

# Pass the lifespan manager to your FastAPI app
app = FastAPI(lifespan=lifespan)

# --- Add Rate Limiter to App ---
# noinspection PyUnresolvedReferences
app.state.limiter = limiter

# Custom rate limit handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]

# --- End Model Loading ---

# Enable CORS - Restrict to coryfitzpatrick.com
# Allowed origins: production domain, localhost for development, and common subdomains
ALLOWED_ORIGINS = [
    "https://coryfitzpatrick.com",
    "https://www.coryfitzpatrick.com",
    "https://fitzmx6.github.io",  # GitHub Pages (HTTPS)
    "http://fitzmx6.github.io",   # GitHub Pages (HTTP, for redirect)
    "http://localhost",
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # FastAPI dev server
    "http://localhost:8080",  # Alternative port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Only allow necessary methods
    allow_headers=["Content-Type", "Authorization"],  # Only allow necessary headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Enable GZIP compression for faster response transfers
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Bot protection middleware - Block known malicious scanners and crawlers
# Note: CORS middleware already restricts browser access to coryfitzpatrick.com
BLOCKED_USER_AGENTS = [
    "masscan", "nmap", "nikto", "sqlmap", "metasploit", "burp",
    "w3af", "acunetix", "nessus", "qualys", "openvas",
    "zap", "skipfish", "wfuzz", "dirb", "dirbuster",
    "semrush", "ahrefsbot", "mj12bot", "dotbot",  # SEO bots
]

@app.middleware("http")
async def bot_protection_middleware(request: Request, call_next):
    """
    Block malicious scanners and unwanted crawlers.
    CORS middleware handles frontend origin restrictions.
    Exempts health check and info endpoints.
    """
    # Allow health checks and root endpoint without restrictions
    if request.url.path in ["/", "/health", "/debug/db"]:
        return await call_next(request)

    user_agent = request.headers.get("user-agent", "").lower()

    # Block known malicious/scanning tools
    for blocked in BLOCKED_USER_AGENTS:
        if blocked in user_agent:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Automated scanning not permitted"}
            )

    response = await call_next(request)
    return response

# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str

# --- Constants ---

# Error message when no relevant context is found
NO_CONTEXT_ERROR_MESSAGE = (
    "I can only answer questions about Cory Fitzpatrick's professional experience, skills, and achievements. "
    "Please ask about his background, technical expertise, or leadership experience."
)

# Load system prompt from environment variable (Cloud Run with Secret Manager) or file (local development)
SYSTEM_PROMPT_FILE = PROJECT_ROOT / "system_prompt.txt"
DEFAULT_SYSTEM_PROMPT = "Portfolio assistant prompt - set via SYSTEM_PROMPT env var or system_prompt.txt file"

# Prioritize environment variable (for Cloud Run with Secret Manager), then fall back to file (for local development)
SYSTEM_PROMPT_TEMPLATE = os.environ.get("SYSTEM_PROMPT")
if SYSTEM_PROMPT_TEMPLATE:
    print("✅ Loading system prompt from SYSTEM_PROMPT environment variable (Secret Manager)...")
elif SYSTEM_PROMPT_FILE.exists():
    print(f"✅ Loading system prompt from {SYSTEM_PROMPT_FILE}...")
    with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT_TEMPLATE = f.read()
else:
    SYSTEM_PROMPT_TEMPLATE = DEFAULT_SYSTEM_PROMPT
    print("⚠️  WARNING: Using default system prompt. Set SYSTEM_PROMPT environment variable or create system_prompt.txt file.")

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
            model=LLM_MODEL_NAME,
            messages=messages,
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
            top_p=GROQ_TOP_P,
            stream=stream
        )

        if stream:
            return response  # Return the streaming response object
        else:
            return response.choices[0].message.content
    except Exception as groq_error:
        print(f"Groq API request failed: {groq_error}")
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
    except Exception as redis_error:
        print(f"Redis get error: {redis_error}")

    return None

def set_cached_response(query: str, response: str, ttl: int = DEFAULT_CACHE_TTL):
    """Cache response in Redis with TTL (default 1 hour)"""
    if not redis_client:
        return

    try:
        cache_key = f"chat:{get_query_hash(query)}"
        redis_client.setex(cache_key, ttl, response)
        print(f"✅ Cached response for query hash: {get_query_hash(query)[:8]}...")
    except Exception as redis_set_error:
        print(f"Redis set error: {redis_set_error}")

def normalize_query(query: str) -> str:
    """Normalize query by removing apostrophes and extra whitespace for better vector search matching"""
    # Remove apostrophes (both straight ' and curly ')
    normalized = query.replace("'", "").replace("'", "")
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    return normalized

def get_relevant_context(request: Request, query: str) -> str:
    """Search vector database for relevant information"""

    # Get models from app.state
    # noinspection PyUnresolvedReferences
    embedding_model = request.app.state.embedding_model
    # noinspection PyUnresolvedReferences
    collection = request.app.state.collection

    # Normalize query for consistent vector search results
    normalized_query = normalize_query(query)

    # Encode query to embedding
    query_embedding = embedding_model.encode([normalized_query]).tolist()

    # Query ChromaDB with similarity filtering
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=N_SEARCH_RESULTS
    )

    if not results['documents'][0]:
        return ""

    # Filter by similarity distance (lower is better, typically 0-2 range)
    # Only include results with distance < threshold (more relevant results)
    context_parts = []
    distances = results.get('distances', [[]])[0] if 'distances' in results else []

    for index, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        # Skip low-quality matches if distance data is available
        if distances and index < len(distances):
            # Skip very dissimilar results (higher distance = less similar)
            if distances[index] > MAX_DISTANCE_THRESHOLD:
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
    except Exception as stream_error:
        print(f"Stream error: {stream_error}")
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

        context = get_relevant_context(request, chat_request.message)

        if not context:
            return ChatResponse(response=NO_CONTEXT_ERROR_MESSAGE)

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
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

    except Exception as chat_error:
        print(f"Error in /api/chat: {str(chat_error)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.post("/api/chat/stream")
@limiter.limit("20/minute")  # 20 requests per minute per IP
async def chat_stream(request: Request, chat_request: ChatRequest):
    """Streaming chat endpoint with rate limiting (no caching for streams)"""
    try:
        # Note: Streaming responses are not cached (harder to cache streams)

        context = get_relevant_context(request, chat_request.message)

        if not context:
            async def error_stream():
                yield NO_CONTEXT_ERROR_MESSAGE
            return StreamingResponse(error_stream(), media_type="text/plain")

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
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

    except Exception as chat_stream_error:
        print(f"Error in /api/chat/stream: {str(chat_stream_error)}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/health")
async def health():
    # This will now respond instantly
    return {"status": "healthy", "model": "llama-3.1-8b-instant", "provider": "groq"}

@app.get("/debug/db")
async def debug_db(request: Request):
    """Debug endpoint to check vector database status"""
    try:
        collection = request.app.state.collection
        count = collection.count()

        # Get a sample document if any exist
        sample = None
        if count > 0:
            results = collection.get(limit=1, include=['metadatas', 'documents'])
            if results and results['ids']:
                sample = {
                    "id": results['ids'][0],
                    "metadata": results['metadatas'][0] if results['metadatas'] else None
                }

        return {
            "status": "ok",
            "database_path": str(DATA_DIR / "chroma_db"),
            "collection_name": "cory_profile",
            "document_count": count,
            "sample_document": sample
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_path": str(DATA_DIR / "chroma_db")
        }

@app.get("/")
async def root():
    """Root endpoint with service status and info"""
    return {
        "service": "Cory Fitzpatrick AI Portfolio Chatbot",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat (POST)",
            "chat_stream": "/api/chat/stream (POST)",
            "debug": "/debug/db (GET)"
        },
        "note": "Service is currently running on Google Cloud Run!",
        "model": "llama-3.1-8b-instant",
        "provider": "groq"
    }


def main():
    """Entry point for running the server"""
    import uvicorn

    # Get port from environment variable, default to 8000
    port = int(os.environ.get("PORT", 8000))

    print(f"🚀 Starting server locally on port {port}...")

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()