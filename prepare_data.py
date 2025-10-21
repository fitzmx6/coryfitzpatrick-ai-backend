# prepare_data.py
import json
import chromadb
from chromadb.config import Settings # <-- ADD THIS IMPORT
from sentence_transformers import SentenceTransformer

def prepare_training_data():
    """Load JSONL and create vector database"""
    
    # Initialize embedding model (runs locally)
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize ChromaDB (persistent storage)
    print("Initializing ChromaDB...")
    # UPDATED LINE TO DISABLE TELEMETRY
    client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
    
    # Create or get collection
    try:
        client.delete_collection("cory_profile")
        print("Deleted existing collection.")
    except Exception:
        pass
    
    collection = client.create_collection(
        name="cory_profile",
        metadata={"description": "Cory Fitzpatrick's professional profile"}
    )
    
    # Load your JSONL file
    print("Loading training data from training_data.jsonl...")
    documents = []
    metadatas = []
    ids = []
    
    try:
        with open('training_data.jsonl', 'r', encoding='utf-8') as f:
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
    except Exception as e:
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
    print("Database saved to ./chroma_db")

if __name__ == "__main__":
    prepare_training_data()