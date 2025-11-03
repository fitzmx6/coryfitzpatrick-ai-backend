import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import json

from cory_ai_chatbot.prepare_data import (
    prepare_training_data,
    main,
    EMBEDDING_MODEL_NAME,
    COLLECTION_NAME,
    PROJECT_ROOT,
    DATA_DIR
)

# ============================================================================
# Test: Constants
# ============================================================================

def test_given_constants_when_imported_then_have_expected_values():
    assert EMBEDDING_MODEL_NAME == 'all-MiniLM-L6-v2'
    assert COLLECTION_NAME == "cory_profile"
    assert DATA_DIR == PROJECT_ROOT / "data"


# ============================================================================
# Test: prepare_training_data - Success Cases
# ============================================================================

@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Q1"}, {"content": "A1"}]}\n{"messages": [{"content": "Q2"}, {"content": "A2"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_valid_jsonl_when_prepare_training_data_then_creates_embeddings(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2], [0.3, 0.4]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify model loaded
    mock_sentence_transformer.assert_called_once_with(EMBEDDING_MODEL_NAME)

    # Verify ChromaDB initialized
    mock_chroma_client.assert_called_once()

    # Verify collection created
    mock_client.create_collection.assert_called_once_with(
        name=COLLECTION_NAME,
        metadata={"description": "Cory Fitzpatrick's professional profile"}
    )

    # Verify embeddings generated
    mock_model.encode.assert_called_once_with(["A1", "A2"])

    # Verify documents added to collection
    mock_collection.add.assert_called_once()
    call_args = mock_collection.add.call_args
    assert call_args[1]['embeddings'] == [[0.1, 0.2], [0.3, 0.4]]
    assert call_args[1]['documents'] == ["A1", "A2"]
    assert len(call_args[1]['metadatas']) == 2
    assert len(call_args[1]['ids']) == 2


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Question"}, {"content": "Answer"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_single_document_when_prepare_training_data_then_processes_correctly(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify single document processed
    call_args = mock_collection.add.call_args
    assert len(call_args[1]['documents']) == 1
    assert call_args[1]['documents'][0] == "Answer"
    assert call_args[1]['metadatas'][0]['question'] == "Question"
    assert call_args[1]['metadatas'][0]['answer'] == "Answer"
    assert call_args[1]['ids'][0] == "doc_0"


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Q1"}, {"content": "A1"}]}\n\n{"messages": [{"content": "Q2"}, {"content": "A2"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_jsonl_with_blank_lines_when_prepare_training_data_then_skips_blanks(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2], [0.3, 0.4]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify only non-blank lines processed
    call_args = mock_collection.add.call_args
    assert len(call_args[1]['documents']) == 2


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Q"}, {"content": "A"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_existing_collection_when_prepare_training_data_then_deletes_old_collection(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify delete attempted
    mock_client.delete_collection.assert_called_once_with(COLLECTION_NAME)


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Q"}, {"content": "A"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_no_existing_collection_when_prepare_training_data_then_handles_gracefully(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_client.delete_collection.side_effect = ValueError("Collection doesn't exist")
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function - should not raise error
    prepare_training_data()

    # Verify still creates new collection
    mock_client.create_collection.assert_called_once()


# ============================================================================
# Test: prepare_training_data - Error Cases
# ============================================================================

@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('cory_ai_chatbot.prepare_data.open', side_effect=FileNotFoundError)
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_missing_jsonl_file_when_prepare_training_data_then_prints_error(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify error message printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("ERROR: training_data.jsonl not found" in str(call) for call in print_calls)


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"invalid": "json"}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_malformed_json_when_prepare_training_data_then_handles_error(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify error message printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("Error reading JSONL" in str(call) for call in print_calls)


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='not valid json at all\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_invalid_json_syntax_when_prepare_training_data_then_handles_error(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify error message printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("Error reading JSONL" in str(call) for call in print_calls)


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_empty_jsonl_file_when_prepare_training_data_then_prints_no_documents(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify no documents message
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("No documents found" in str(call) for call in print_calls)


@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='   \n\n   \n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_only_whitespace_when_prepare_training_data_then_prints_no_documents(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify no documents message
    print_calls = [str(call) for call in mock_print.call_args_list]
    assert any("No documents found" in str(call) for call in print_calls)


# ============================================================================
# Test: main
# ============================================================================

@patch('cory_ai_chatbot.prepare_data.prepare_training_data')
def test_given_main_called_when_executed_then_calls_prepare_training_data(mock_prepare):
    main()
    mock_prepare.assert_called_once()


# ============================================================================
# Test: Metadata Structure
# ============================================================================

@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "What is Python?"}, {"content": "Python is a programming language"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_document_when_prepare_training_data_then_metadata_has_correct_structure(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify metadata structure
    call_args = mock_collection.add.call_args
    metadata = call_args[1]['metadatas'][0]
    assert 'question' in metadata
    assert 'answer' in metadata
    assert 'id' in metadata
    assert metadata['question'] == "What is Python?"
    assert metadata['answer'] == "Python is a programming language"
    assert metadata['id'] == 0


# ============================================================================
# Test: Path Configuration
# ============================================================================

@patch('cory_ai_chatbot.prepare_data.SentenceTransformer')
@patch('cory_ai_chatbot.prepare_data.chromadb.PersistentClient')
@patch('builtins.open', new_callable=mock_open, read_data='{"messages": [{"content": "Q"}, {"content": "A"}]}\n')
@patch('cory_ai_chatbot.prepare_data.print')
def test_given_prepare_training_data_when_called_then_uses_correct_paths(
    mock_print, mock_file, mock_chroma_client, mock_sentence_transformer
):
    # Setup mocks
    mock_model = Mock()
    mock_sentence_transformer.return_value = mock_model
    mock_model.encode.return_value.tolist.return_value = [[0.1]]

    mock_client = Mock()
    mock_chroma_client.return_value = mock_client
    mock_collection = Mock()
    mock_client.create_collection.return_value = mock_collection

    # Run function
    prepare_training_data()

    # Verify ChromaDB path
    call_args = mock_chroma_client.call_args
    assert 'chroma_db' in str(call_args[1]['path'])
