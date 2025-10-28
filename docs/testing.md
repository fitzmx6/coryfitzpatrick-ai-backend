# Test Suite Documentation

This document describes the test suite for the Cory AI Chatbot project.

## Test Structure

The test suite follows these conventions:

### Naming Format
- **Given-When-Then**: Test names use the format `test_given_[context]_when_[action]_then_[outcome]`

### Test Data
- Superhero names are used for test data properties (Spider-Man, Batman, Wonder Woman, etc.)
- Makes tests more readable and memorable

## Test Files

### test_server.py (24 tests)
Tests for `server.py` covering:
- `get_query_hash()` - Query hashing functionality
- `get_cached_response()` - Redis cache retrieval
- `set_cached_response()` - Redis cache storage
- `get_relevant_context()` - Vector database queries
- `query_groq()` - LLM API calls
- API endpoints (`/api/chat`, `/health`, `/`)

### test_chat_client.py (15 tests)
Tests for `chat_client.py` covering:
- `send_question()` - Streaming API requests
- `print_welcome()` - Welcome message display
- Conversation history management
- Error handling for network issues

### Note on prepare_data.py
Tests for `prepare_data.py` are not included due to complex external dependencies (ChromaDB, file I/O).
To add tests for this module, consider refactoring to separate concerns:
- File reading logic
- Data validation logic
- Embedding generation logic
- Database interaction logic

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest test_server.py
pytest test_chat_client.py
```

### Run Specific Test
```bash
pytest test_server.py::test_given_query_when_hash_generated_then_returns_md5_hash
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage Report
```bash
pytest --cov=. --cov-report=html
```
This generates an HTML coverage report in `htmlcov/index.html`

### Run Tests by Marker (if you add markers)
```bash
pytest -m unit        # Run only unit tests
pytest -m integration # Run only integration tests
pytest -m "not slow"  # Skip slow tests
```

## Test Coverage

The test suite provides comprehensive coverage of:
- ✅ Core business logic functions
- ✅ API endpoints
- ✅ Error handling and edge cases
- ✅ Data processing and validation
- ✅ Caching mechanisms
- ✅ Streaming responses
- ✅ Conversation history management

## Writing New Tests

When adding new tests, follow these guidelines:

1. **Use Given-When-Then naming**:
   ```python
   def test_given_valid_input_when_process_then_returns_result():
   ```

2. **Use superhero names for test data**:
   ```python
   user_name = "Peter Parker"
   hero_alias = "Spider-Man"
   ```

3. **Mock external dependencies**:
   ```python
   @patch('module.external_api')
   def test_function(mock_api):
       mock_api.return_value = "Wonder Woman"
   ```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
```

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the project root:
```bash
cd /path/to/cory-ai-chatbot
pytest
```

### Module Not Found
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Redis Tests Failing
Redis tests use mocks, so Redis doesn't need to be running. If tests fail, check that mocks are properly configured.

## Test Maintenance

- Keep tests independent and isolated
- Update tests when changing functionality
- Add tests for new features
- Remove tests for deprecated features
- Keep test data relevant and clear
