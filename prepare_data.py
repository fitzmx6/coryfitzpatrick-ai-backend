# prepare_data.py
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

def prepare_training_data():
    """Load JSONL and create vector database"""
    
    # Initialize embedding model (runs locally)
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize ChromaDB (persistent storage)
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or get collection
    try:
        collection = client.delete_collection("cory_profile")
    except:
        pass
    
    collection = client.create_collection(
        name="cory_profile",
        metadata={"description": "Cory Fitzpatrick's professional profile"}
    )
    
    # Load your JSONL file
    print("Loading training data...")
    documents = []
    metadatas = []
    ids = []
    
    with open('training_data.jsonl', 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if line.strip():
                data = json.loads(line)
                messages = data['messages']
                
                # Extract question and answer
                question = messages[0]['content']
                answer = messages[1]['content']
                
                # Store the answer as the document
                documents.append(answer)
                metadatas.append({
                    "question": question,
                    "answer": answer,
                    "id": idx
                })
                ids.append(f"doc_{idx}")
    
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