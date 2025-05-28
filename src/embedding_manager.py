"""Vector embeddings management using Chroma DB for RAG"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import ollama
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from config.settings import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

class EmbeddingManager:
    """Manages vector embeddings using Chroma DB"""
    
    def __init__(self, use_ollama: bool = True, progress_callback=None):
        self.use_ollama = use_ollama
        self.progress_callback = progress_callback
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(
                anonymized_telemetry=False,  # Disable telemetry for privacy
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=CHROMA_COLLECTION_NAME
            )
            print(f"📖 Loaded existing collection with {self.collection.count()} documents")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=self._get_embedding_function()
            )
            print("✨ Created new Chroma collection")
        
        print("✅ Chroma embedding manager initialized")
    
    def _get_embedding_function(self):
        """Get the embedding function for Chroma"""
        if self.use_ollama:
            return chromadb.utils.embedding_functions.OllamaEmbeddingFunction(
                url="http://localhost:11434",
                model_name=EMBEDDING_MODEL,
            )
        else:
            return chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
    
    def add_chunks(self, chunks: List[Dict]) -> bool:
        """Add document chunks to Chroma collection"""
        if not chunks:
            print("⚠️ No chunks to add")
            if self.progress_callback:
                self.progress_callback("⚠️ No chunks to add", 0, 1, "no_chunks")
            return False
        
        print(f"🧠 Adding {len(chunks)} chunks to Chroma collection...")
        
        # Update UI with embedding progress
        if self.progress_callback:
            self.progress_callback(f"Generating embeddings for {len(chunks)} chunks...", 0, len(chunks), "embedding_start")
        
        try:
            # Prepare data for Chroma
            documents = [chunk['content'] for chunk in chunks]
            metadatas = [{
                'source': chunk['source'],
                'chunk_id': chunk['id'],
                'metadata': str(chunk.get('metadata', {}))
            } for chunk in chunks]
            ids = [chunk['id'] for chunk in chunks]
            
            # If we have many chunks, add them in batches to provide better progress updates
            batch_size = 10
            if len(chunks) > batch_size and self.progress_callback:
                # Process in batches with progress updates
                for i in range(0, len(chunks), batch_size):
                    batch_end = min(i + batch_size, len(chunks))
                    batch_documents = documents[i:batch_end]
                    batch_metadatas = metadatas[i:batch_end]
                    batch_ids = ids[i:batch_end]
                    
                    # Update UI with batch progress
                    self.progress_callback(
                        f"Embedding batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size} ({i}/{len(chunks)} chunks)",
                        i,
                        len(chunks),
                        f"batch_{i // batch_size}"
                    )
                    
                    # Add batch to collection
                    self.collection.add(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
            else:
                # Add all at once for smaller collections
                if self.progress_callback:
                    self.progress_callback(f"Embedding all {len(chunks)} chunks", 0, len(chunks), "embedding_all")
                
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            print(f"✅ Added {len(chunks)} chunks to collection")
            print(f"📊 Total documents in collection: {self.collection.count()}")
            
            # Final progress update
            if self.progress_callback:
                self.progress_callback(
                    f"✅ Successfully added {len(chunks)} chunks to vector database",
                    len(chunks),
                    len(chunks),
                    "embedding_complete"
                )
                
            return True
            
        except Exception as e:
            print(f"❌ Error adding chunks to Chroma: {e}")
            if self.progress_callback:
                self.progress_callback(f"❌ Error: {str(e)}", 0, 1, "error")
            return False
    
    def find_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find most similar chunks using Chroma's vector search"""
        if self.collection.count() == 0:
            print("❌ No documents in collection!")
            return []
        
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count())
            )
            
            # Convert results to our format
            similar_chunks = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    chunk = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'source': results['metadatas'][0][i]['source'],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'metadata': results['metadatas'][0][i]
                    }
                    similar_chunks.append(chunk)
            
            print(f"🔍 Found {len(similar_chunks)} similar chunks")
            return similar_chunks
            
        except Exception as e:
            print(f"❌ Error querying Chroma: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            
            if count > 0:
                # Get a sample to analyze sources  
                sample = self.collection.get(limit=min(100, count))
                sources = set()
                if sample['metadatas']:
                    sources = set(meta['source'] for meta in sample['metadatas'])
                
                return {
                    'total_chunks': count,
                    'unique_sources': len(sources),
                    'sources': list(sources),
                    'status': 'Ready'
                }
            else:
                return {
                    'total_chunks': 0,
                    'unique_sources': 0,
                    'sources': [],
                    'status': 'Empty'
                }
                
        except Exception as e:
            return {
                'status': f'Error: {str(e)}',
                'total_chunks': 0
            }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(CHROMA_COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=CHROMA_COLLECTION_NAME,
                embedding_function=self._get_embedding_function()
            )
            print("🗑️ Collection cleared")
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")