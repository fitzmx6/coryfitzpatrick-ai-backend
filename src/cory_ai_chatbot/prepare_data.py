# prepare_data.py
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Determine the project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def prepare_training_data():
    """Load JSONL and create vector database"""

    # Initialize embedding model (runs locally)
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    # Initialize ChromaDB (persistent storage)
    print("Initializing ChromaDB...")
    chroma_path = DATA_DIR / "chroma_db"
    client = chromadb.PersistentClient(path=str(chroma_path), settings=Settings(anonymized_telemetry=False))
    
    # Create or get collection
    try:
        client.delete_collection("cory_profile")
        print("Deleted existing collection.")
    except ValueError:
        # Collection doesn't exist, which is fine
        pass
    
    collection = client.create_collection(
        name="cory_profile",
        metadata={"description": "Cory Fitzpatrick's professional profile"}
    )
    
    # Load your JSONL file
    training_data_path = DATA_DIR / "training_data.jsonl"
    print(f"Loading training data from {training_data_path}...")
    documents = []
    metadatas = []
    ids = []

    try:
        with open(training_data_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if line.strip():
                    data = json.loads(line)
                    # Use 'messages' format
                    question = data['messages'][0]['content']
                    answer = data['messages'][1]['content']
                    
                    documents.append(answer) # Embed and store the answer
                    metadatas.append({
                        "question": question,
                        "answer": answer, # Store answer in metadata too
                        "id": idx
                    })
                    ids.append(f"doc_{idx}")
    except FileNotFoundError:
        print("ERROR: training_data.jsonl not found.")
        return
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error reading JSONL: {e}")
        return

    if not documents:
        print("No documents found in training_data.jsonl.")
        return
        
    print(f"Processing {len(documents)} documents...")
    
    # Generate embeddings
    embeddings = embedding_model.encode(documents).tolist()
    
    # Add to ChromaDB
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"✅ Successfully stored {len(documents)} documents in vector database!")
    print(f"Database saved to {chroma_path}")

def main():
    """Entry point for CLI"""
    prepare_training_data()

if __name__ == "__main__":
    main()