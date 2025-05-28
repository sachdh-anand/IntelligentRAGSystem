"""Configuration settings for the RAG system"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
PROCESSED_DIR = PROJECT_ROOT / "processed"
CHUNKS_DIR = PROCESSED_DIR / "chunks"
EMBEDDINGS_DIR = PROCESSED_DIR / "embeddings"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "phi3:mini"
EMBEDDING_MODEL = "nomic-embed-text"

# Processing settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_RELEVANT_CHUNKS = 5

# Chroma settings
CHROMA_DB_PATH = PROCESSED_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = "document_chunks"

# Create directories if they don't exist
for dir_path in [DOCUMENTS_DIR, PROCESSED_DIR, CHUNKS_DIR, EMBEDDINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
