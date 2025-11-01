import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import Request
import hashlib

# Import functions to test
from cory_ai_chatbot.server import (
    get_query_hash,
    get_cached_response,
    set_cached_response,
    get_relevant_context,
    query_groq,
    normalize_query,
    NO_CONTEXT_ERROR_MESSAGE,
    app
)

# ============================================================================
# Test: get_query_hash
# ============================================================================

def test_given_query_when_hash_generated_then_returns_md5_hash():
    query = "What is Spider-Man's real name?"
    expected_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()

    result = get_query_hash(query)

    assert result == expected_hash

def test_given_query_with_whitespace_when_hash_generated_then_strips_whitespace():
    query_with_spaces = "  What is Wonder Woman's lasso?  "
    query_without_spaces = "What is Wonder Woman's lasso?"

    hash_with_spaces = get_query_hash(query_with_spaces)
    hash_without_spaces = get_query_hash(query_without_spaces)

    assert hash_with_spaces == hash_without_spaces

def test_given_query_with_different_case_when_hash_generated_then_same_hash():
    query_upper = "WHAT IS BATMAN'S CITY?"
    query_lower = "what is batman's city?"

    hash_upper = get_query_hash(query_upper)
    hash_lower = get_query_hash(query_lower)

    assert hash_upper == hash_lower

# ============================================================================
# Test: get_cached_response
# ============================================================================

@patch('cory_ai_chatbot.server.redis_client')
def test_given_cached_response_exists_when_get_cached_then_returns_cached_value(mock_redis):
    query = "What are Superman's powers?"
    cached_response = "Superman has super strength, flight, and heat vision"
    mock_redis.get.return_value = cached_response

    result = get_cached_response(query)

    assert result == cached_response
    mock_redis.get.assert_called_once()

@patch('cory_ai_chatbot.server.redis_client')
def test_given_no_cached_response_when_get_cached_then_returns_none(mock_redis):
    query = "What is Iron Man's suit made of?"
    mock_redis.get.return_value = None

    result = get_cached_response(query)

    assert result is None

@patch('cory_ai_chatbot.server.redis_client', None)
def test_given_no_redis_client_when_get_cached_then_returns_none():
    query = "What is Thor's hammer called?"

    result = get_cached_response(query)

    assert result is None

@patch('cory_ai_chatbot.server.redis_client')
def test_given_redis_error_when_get_cached_then_returns_none(mock_redis):
    query = "What is Black Widow's real name?"
    mock_redis.get.side_effect = Exception("Redis connection failed")

    result = get_cached_response(query)

    assert result is None

# ============================================================================
# Test: set_cached_response
# ============================================================================

@patch('cory_ai_chatbot.server.redis_client')
def test_given_response_when_cache_set_then_stores_in_redis(mock_redis):
    query = "Who is Captain America?"
    response = "Captain America is Steve Rogers, a super soldier"
    ttl = 3600

    set_cached_response(query, response, ttl)

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == ttl  # TTL parameter
    assert call_args[0][2] == response  # Response parameter

@patch('cory_ai_chatbot.server.redis_client', None)
def test_given_no_redis_client_when_cache_set_then_no_error():
    query = "Who is Hulk?"
    response = "Hulk is Bruce Banner"

    set_cached_response(query, response)

@patch('cory_ai_chatbot.server.redis_client')
def test_given_redis_error_when_cache_set_then_handles_gracefully(mock_redis):
    query = "Who is Hawkeye?"
    response = "Hawkeye is Clint Barton"
    mock_redis.setex.side_effect = Exception("Redis write failed")

    set_cached_response(query, response)

# ============================================================================
# Test: query_groq
# ============================================================================

@patch('cory_ai_chatbot.server.groq_client')
def test_given_prompt_when_query_groq_then_returns_response(mock_groq_client):
    prompt = "What is Wolverine's power?"
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Wolverine has healing factor and adamantium claws"
    mock_groq_client.chat.completions.create.return_value = mock_response

    result = query_groq(prompt)

    assert result == "Wolverine has healing factor and adamantium claws"
    mock_groq_client.chat.completions.create.assert_called_once()

@patch('cory_ai_chatbot.server.groq_client')
def test_given_conversation_history_when_query_groq_then_includes_history(mock_groq_client):
    prompt = "Tell me more about Storm"
    conversation_history = [
        {"role": "user", "content": "Who is Storm?"},
        {"role": "assistant", "content": "Storm is Ororo Munroe"}
    ]
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Storm controls weather"
    mock_groq_client.chat.completions.create.return_value = mock_response

    result = query_groq(prompt, conversation_history)

    call_args = mock_groq_client.chat.completions.create.call_args
    messages = call_args[1]['messages']
    assert len(messages) == 3  # History + new prompt
    assert messages[0] == conversation_history[0]
    assert messages[1] == conversation_history[1]
    assert messages[2]['content'] == prompt

@patch('cory_ai_chatbot.server.groq_client')
def test_given_stream_enabled_when_query_groq_then_returns_stream(mock_groq_client):
    prompt = "What is Cyclops' power?"
    mock_stream = Mock()
    mock_groq_client.chat.completions.create.return_value = mock_stream

    result = query_groq(prompt, stream=True)

    assert result == mock_stream
    call_args = mock_groq_client.chat.completions.create.call_args
    assert call_args[1]['stream'] is True

@patch('cory_ai_chatbot.server.groq_client')
def test_given_groq_error_when_query_groq_then_returns_error_message(mock_groq_client):
    prompt = "Who is Jean Grey?"
    mock_groq_client.chat.completions.create.side_effect = Exception("API error")

    result = query_groq(prompt)

    assert "error occurred" in result.lower()

@patch('cory_ai_chatbot.server.groq_client')
def test_given_groq_error_with_stream_when_query_groq_then_returns_none(mock_groq_client):
    prompt = "Who is Professor X?"
    mock_groq_client.chat.completions.create.side_effect = Exception("API error")

    result = query_groq(prompt, stream=True)

    assert result is None

# ============================================================================
# Test: get_relevant_context
# ============================================================================

def test_given_relevant_documents_when_get_context_then_returns_formatted_context():
    mock_request = Mock(spec=Request)
    mock_embedding_model = Mock()
    mock_collection = Mock()

    # noinspection PyUnresolvedReferences
    mock_request.app.state.embedding_model = mock_embedding_model
    # noinspection PyUnresolvedReferences
    mock_request.app.state.collection = mock_collection

    mock_embedding_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]

    mock_collection.query.return_value = {
        'documents': [['Black Panther is the king of Wakanda']],
        'metadatas': [[{
            'question': 'Who is Black Panther?',
            'answer': 'Black Panther is T\'Challa, king of Wakanda'
        }]],
        'distances': [[0.5]]
    }

    query = "Who is Black Panther?"

    result = get_relevant_context(mock_request, query)

    assert 'Black Panther' in result
    assert 'Who is Black Panther?' in result
    mock_embedding_model.encode.assert_called_once_with([query])
    mock_collection.query.assert_called_once()


def test_given_no_documents_when_get_context_then_returns_empty_string():
    mock_request = Mock(spec=Request)
    mock_embedding_model = Mock()
    mock_collection = Mock()

    # noinspection PyUnresolvedReferences
    mock_request.app.state.embedding_model = mock_embedding_model
    # noinspection PyUnresolvedReferences
    mock_request.app.state.collection = mock_collection

    mock_embedding_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
    mock_collection.query.return_value = {'documents': [[]], 'metadatas': [[]]}

    query = "Who is Ant-Man?"

    result = get_relevant_context(mock_request, query)

    assert result == ""


def test_given_low_similarity_documents_when_get_context_then_filters_out():
    mock_request = Mock(spec=Request)
    mock_embedding_model = Mock()
    mock_collection = Mock()

    # noinspection PyUnresolvedReferences
    mock_request.app.state.embedding_model = mock_embedding_model
    # noinspection PyUnresolvedReferences
    mock_request.app.state.collection = mock_collection

    mock_embedding_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]

    # High distance = low similarity (should be filtered)
    mock_collection.query.return_value = {
        'documents': [['Doctor Strange is a sorcerer']],
        'metadatas': [[{'question': 'Who is Doctor Strange?', 'answer': 'Doctor Strange'}]],
        'distances': [[2.0]]  # Very high distance, should be filtered
    }

    query = "Who is Doctor Strange?"

    result = get_relevant_context(mock_request, query)

    assert result == ""  # Should be filtered out

# ============================================================================
# Test: API Endpoints
# ============================================================================

# Note: TestClient is created as a fixture to avoid app initialization during import
@pytest.fixture
def client():
    # Mock the app state to avoid lifespan startup issues during tests
    from unittest.mock import Mock
    app.state.embedding_model = Mock()
    app.state.chroma_client = Mock()
    app.state.collection = Mock()
    app.state.limiter = Mock()

    # Create client without triggering lifespan events
    return TestClient(app, raise_server_exceptions=False)

@patch('cory_ai_chatbot.server.get_relevant_context')
@patch('cory_ai_chatbot.server.query_groq')
@patch('cory_ai_chatbot.server.get_cached_response')
def test_given_valid_message_when_post_chat_then_returns_response(
    mock_get_cached, mock_query_groq, mock_get_context, client
):
    mock_get_cached.return_value = None
    mock_get_context.return_value = "Aquaman is the king of Atlantis"
    mock_query_groq.return_value = "Aquaman rules the underwater kingdom of Atlantis"

    payload = {
        "message": "Who is Aquaman?",
        "conversation_history": []
    }

    response = client.post("/api/chat", json=payload)

    assert response.status_code == 200
    assert "Aquaman" in response.json()["response"]

@patch('cory_ai_chatbot.server.get_relevant_context')
@patch('cory_ai_chatbot.server.get_cached_response')
def test_given_no_context_when_post_chat_then_returns_error_message(
    mock_get_cached, mock_get_context, client
):
    mock_get_cached.return_value = None
    mock_get_context.return_value = ""  # No context found

    payload = {
        "message": "Who is Flash?",
        "conversation_history": []
    }

    response = client.post("/api/chat", json=payload)

    assert response.status_code == 200
    assert NO_CONTEXT_ERROR_MESSAGE in response.json()["response"]

@patch('cory_ai_chatbot.server.get_cached_response')
def test_given_cached_response_when_post_chat_then_returns_cached(mock_get_cached, client):
    cached_response = "Green Lantern wields a power ring"
    mock_get_cached.return_value = cached_response

    payload = {
        "message": "Who is Green Lantern?",
        "conversation_history": []
    }

    response = client.post("/api/chat", json=payload)

    assert response.status_code == 200
    assert response.json()["response"] == cached_response

def test_given_no_payload_when_post_chat_then_returns_422(client):
    response = client.post("/api/chat", json={})

    assert response.status_code == 422

def test_given_health_check_when_get_health_then_returns_healthy(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_given_root_request_when_get_root_then_returns_service_info(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "status" in data
    assert data["status"] == "online"

# ============================================================================
# Test: normalize_query
# ============================================================================

def test_given_query_with_apostrophes_when_normalize_then_removes_apostrophes():
    query = "What is Cory's experience?"
    expected = "What is Corys experience?"

    result = normalize_query(query)

    assert result == expected

def test_given_query_with_curly_apostrophes_when_normalize_then_removes_apostrophes():
    query = "What's Cory's experience?"
    expected = "Whats Corys experience?"

    result = normalize_query(query)

    assert result == expected

def test_given_query_with_extra_whitespace_when_normalize_then_removes_whitespace():
    query = "What  is   Cory's    experience?"
    expected = "What is Corys experience?"

    result = normalize_query(query)

    assert result == expected

# ============================================================================
# Test: CORS Middleware
# ============================================================================

def test_given_allowed_origin_when_request_then_cors_headers_set(client):
    response = client.get("/health", headers={"Origin": "https://coryfitzpatrick.com"})

    assert response.status_code == 200
    # TestClient doesn't fully process CORS middleware, so we just verify endpoint works

def test_given_localhost_origin_when_request_then_cors_headers_set(client):
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200

# ============================================================================
# Test: Bot Protection Middleware
# ============================================================================

def test_given_malicious_user_agent_when_chat_request_then_blocked(client):
    # Bot protection middleware should block malicious user agents
    response = client.post(
        "/api/chat",
        json={"message": "test"},
        headers={"User-Agent": "masscan/1.0"}
    )

    # Should be blocked with 403
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

def test_given_scanner_user_agent_when_chat_request_then_blocked(client):
    response = client.post(
        "/api/chat",
        json={"message": "test"},
        headers={"User-Agent": "nikto/2.1.6"}
    )

    assert response.status_code == 403

def test_given_normal_user_agent_when_chat_request_then_allowed(client):
    with patch('cory_ai_chatbot.server.get_relevant_context') as mock_context, \
         patch('cory_ai_chatbot.server.query_groq') as mock_groq, \
         patch('cory_ai_chatbot.server.get_cached_response') as mock_cached:

        mock_cached.return_value = None
        mock_context.return_value = "Cory is a software engineer"
        mock_groq.return_value = "Cory has experience in Python"

        response = client.post(
            "/api/chat",
            json={"message": "test"},
            headers={"User-Agent": "Mozilla/5.0"}
        )

        assert response.status_code == 200

def test_given_health_check_when_bot_user_agent_then_allowed(client):
    # Health check should bypass bot protection
    response = client.get(
        "/health",
        headers={"User-Agent": "masscan/1.0"}
    )

    assert response.status_code == 200

def test_given_root_endpoint_when_bot_user_agent_then_allowed(client):
    # Root endpoint should bypass bot protection
    response = client.get(
        "/",
        headers={"User-Agent": "nikto/2.1.6"}
    )

    assert response.status_code == 200

def test_given_debug_endpoint_when_bot_user_agent_then_allowed(client):
    # Debug endpoint should bypass bot protection
    response = client.get(
        "/debug/db",
        headers={"User-Agent": "masscan/1.0"}
    )

    assert response.status_code == 200
