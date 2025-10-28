from unittest.mock import Mock, patch
from io import StringIO

# Import functions to test
from cory_ai_chatbot.cli import send_question, print_welcome

# ============================================================================
# Test: send_question
# ============================================================================

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_valid_question_when_send_question_then_returns_response(mock_post):
    question = "What is Superman's weakness?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([
        "Superman's weakness is ",
        "kryptonite"
    ])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert result == "Superman's weakness is kryptonite"
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]['json']['message'] == question
    assert call_args[1]['stream'] is True

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_conversation_history_when_send_question_then_includes_history(mock_post):
    question = "Tell me more about Batman"
    conversation_history = [
        {"role": "user", "content": "Who is Batman?"},
        {"role": "assistant", "content": "Batman is Bruce Wayne"}
    ]
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter(["Batman is a vigilante"])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    call_args = mock_post.call_args
    assert call_args[1]['json']['conversation_history'] == conversation_history

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_connection_error_when_send_question_then_returns_none(mock_post):
    import requests
    question = "Who is Wonder Woman?"
    conversation_history = []
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

    result = send_question(question, conversation_history)

    assert result is None

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_timeout_when_send_question_then_returns_none(mock_post):
    import requests
    question = "Who is Flash?"
    conversation_history = []
    mock_post.side_effect = requests.exceptions.Timeout()

    result = send_question(question, conversation_history)

    assert result is None

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_http_error_when_send_question_then_returns_none(mock_post):
    import requests
    question = "Who is Aquaman?"
    conversation_history = []
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert result is None

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_empty_response_when_send_question_then_returns_empty_string(mock_post):
    question = "Who is Green Lantern?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert result == ""

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_chunked_response_when_send_question_then_concatenates_chunks(mock_post):
    question = "Who is Spider-Man?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([
        "Spider-Man ",
        "is ",
        "Peter ",
        "Parker, ",
        "a ",
        "superhero"
    ])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert result == "Spider-Man is Peter Parker, a superhero"

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_none_chunks_when_send_question_then_skips_none_values(mock_post):
    question = "Who is Iron Man?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([
        "Iron Man ",
        None,
        "is ",
        None,
        "Tony Stark"
    ])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert result == "Iron Man is Tony Stark"

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_question_when_send_question_then_sets_correct_timeout(mock_post):
    question = "Who is Thor?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter(["Thor is the God of Thunder"])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    call_args = mock_post.call_args
    assert call_args[1]['timeout'] == 30

# ============================================================================
# Test: print_welcome
# ============================================================================

@patch('sys.stdout', new_callable=StringIO)
def test_given_print_welcome_when_called_then_displays_welcome_message(mock_stdout):
    print_welcome()

    output = mock_stdout.getvalue()
    assert "Welcome to Cory Fitzpatrick's AI Portfolio Chatbot" in output
    assert "Work experience" in output
    assert "Technical skills" in output
    assert "quit" in output or "exit" in output

@patch('sys.stdout', new_callable=StringIO)
def test_given_print_welcome_when_called_then_includes_formatting(mock_stdout):
    print_welcome()

    output = mock_stdout.getvalue()
    assert "=" in output  # Should have separator lines

# ============================================================================
# Test: Integration Scenarios
# ============================================================================

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_multiple_questions_when_send_question_then_builds_history(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200

    # First question
    mock_response.iter_content.return_value = iter(["Black Panther is T'Challa"])
    mock_post.return_value = mock_response

    conversation_history = []
    question1 = "Who is Black Panther?"

    response1 = send_question(question1, conversation_history)
    conversation_history.append({"role": "user", "content": question1})
    conversation_history.append({"role": "assistant", "content": response1})

    # Second question
    mock_response.iter_content.return_value = iter(["Wakanda is in Africa"])
    question2 = "Where is Wakanda?"
    response2 = send_question(question2, conversation_history)

    assert len(conversation_history) == 2
    assert conversation_history[0]["content"] == question1
    assert conversation_history[1]["content"] == response1
    assert response2 == "Wakanda is in Africa"

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_special_characters_when_send_question_then_handles_correctly(mock_post):
    question = "What is Doctor Strange's artifact?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([
        "Doctor Strange wields the Eye of Agamotto"
    ])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert "Doctor Strange" in result
    assert "Eye of Agamotto" in result

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_long_response_when_send_question_then_handles_all_chunks(mock_post):
    question = "Tell me about Wolverine"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200

    # Create 50 small chunks to simulate long response
    chunks = [f"chunk{i} " for i in range(50)]
    mock_response.iter_content.return_value = iter(chunks)
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    for i in range(50):
        assert f"chunk{i}" in result
    assert len(result) > 0

@patch('cory_ai_chatbot.cli.requests.post')
def test_given_unicode_response_when_send_question_then_handles_unicode(mock_post):
    question = "Who is Shang-Chi?"
    conversation_history = []
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = iter([
        "Shang-Chi is a martial arts master 🥋"
    ])
    mock_post.return_value = mock_response

    result = send_question(question, conversation_history)

    assert "Shang-Chi" in result
    assert "martial arts" in result
