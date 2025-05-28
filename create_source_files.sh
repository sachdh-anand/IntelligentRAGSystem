#!/bin/bash

# Create Missing Source Files for RAG System
echo "🔧 Creating missing source files..."

# Create src/document_processor.py
cat > src/document_processor.py << 'EOF'
"""Document processing using Docling"""
import json
from pathlib import Path
from typing import List, Dict
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionResult
from config.settings import DOCUMENTS_DIR, CHUNKS_DIR

class DoclingProcessor:
    """High-quality document processing using Docling"""
    
    def __init__(self):
        self.converter = DocumentConverter()
        print("✅ Docling processor initialized")
    
    def process_document(self, file_path: Path) -> Dict:
        """Process a single document with Docling"""
        print(f"📄 Processing: {file_path.name}")
        
        try:
            # Convert document using Docling
            result: ConversionResult = self.converter.convert(str(file_path))
            
            # Extract structured content
            document_data = {
                'filename': file_path.name,
                'path': str(file_path),
                'content': result.document.export_to_markdown(),
                'metadata': {
                    'pages': len(result.document.pages) if hasattr(result.document, 'pages') else 1,
                    'elements': len(result.document.texts) if hasattr(result.document, 'texts') else 0,
                    'tables': len(result.document.tables) if hasattr(result.document, 'tables') else 0,
                }
            }
            
            print(f"  ✅ Extracted {len(document_data['content'])} characters")
            return document_data
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            return None
    
    def create_chunks(self, document_data: Dict, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Split document into overlapping chunks"""
        content = document_data['content']
        filename = document_data['filename']
        
        # Simple sentence-aware chunking
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        'id': f"{filename}_chunk_{len(chunks)}",
                        'content': current_chunk.strip(),
                        'source': filename,
                        'metadata': document_data['metadata']
                    })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'id': f"{filename}_chunk_{len(chunks)}",
                'content': current_chunk.strip(),
                'source': filename,
                'metadata': document_data['metadata']
            })
        
        print(f"  📑 Created {len(chunks)} chunks")
        return chunks
    
    def process_all_documents(self) -> List[Dict]:
        """Process all documents in the documents directory"""
        all_chunks = []
        supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.html'}
        
        print(f"🔍 Scanning {DOCUMENTS_DIR} for documents...")
        
        document_files = [
            f for f in DOCUMENTS_DIR.rglob('*') 
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not document_files:
            print("❌ No supported documents found!")
            print(f"   Supported formats: {', '.join(supported_extensions)}")
            return []
        
        print(f"📚 Found {len(document_files)} documents to process")
        
        for file_path in document_files:
            document_data = self.process_document(file_path)
            if document_data:
                chunks = self.create_chunks(document_data)
                all_chunks.extend(chunks)
                
                # Save chunks to file
                chunk_file = CHUNKS_DIR / f"{file_path.stem}_chunks.json"
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Total processed: {len(all_chunks)} chunks from {len(document_files)} documents")
        return all_chunks

# Test the processor
if __name__ == "__main__":
    processor = DoclingProcessor()
    chunks = processor.process_all_documents()
    print(f"Processed {len(chunks)} chunks total")
EOF

# Create src/embedding_manager.py
cat > src/embedding_manager.py << 'EOF'
"""Vector embeddings management using Chroma DB for RAG"""
import ollama
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
from config.settings import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

class EmbeddingManager:
    """Manages vector embeddings using Chroma DB"""
    
    def __init__(self, use_ollama: bool = True):
        self.use_ollama = use_ollama
        
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
                name=CHROMA_COLLECTION_NAME,
                embedding_function=self._get_embedding_function()
            )
            print(f"📖 Loaded existing collection with {self.collection.count()} documents")
        except ValueError:
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
            return False
        
        print(f"🧠 Adding {len(chunks)} chunks to Chroma collection...")
        
        try:
            # Prepare data for Chroma
            documents = [chunk['content'] for chunk in chunks]
            metadatas = [{
                'source': chunk['source'],
                'chunk_id': chunk['id'],
                'metadata': str(chunk.get('metadata', {}))
            } for chunk in chunks]
            ids = [chunk['id'] for chunk in chunks]
            
            # Add to collection (Chroma handles embedding generation)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(chunks)} chunks to collection")
            print(f"📊 Total documents in collection: {self.collection.count()}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding chunks to Chroma: {e}")
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
EOF

# Create src/rag_system.py
cat > src/rag_system.py << 'EOF'
"""Main RAG system combining all components"""
import ollama
from typing import List, Dict
from document_processor import DoclingProcessor
from embedding_manager import EmbeddingManager
from config.settings import LLM_MODEL, MAX_RELEVANT_CHUNKS

class RAGSystem:
    """Complete RAG system using Docling + Ollama"""
    
    def __init__(self):
        self.processor = DoclingProcessor()
        self.embedding_manager = EmbeddingManager()
        
        print("🚀 RAG System initialized")
        self._load_or_process_documents()
    
    def _load_or_process_documents(self):
        """Load existing embeddings or process documents"""
        # Check if we have documents in Chroma
        stats = self.embedding_manager.get_collection_stats()
        
        if stats['total_chunks'] > 0:
            print(f"📚 Found existing collection with {stats['total_chunks']} chunks")
            return
        
        print("📚 No existing collection found. Processing documents...")
        self._process_documents()
    
    def _process_documents(self):
        """Process all documents and add to Chroma"""
        # Process documents with Docling
        chunks = self.processor.process_all_documents()
        
        if chunks:
            # Add to Chroma (handles embedding generation automatically)
            success = self.embedding_manager.add_chunks(chunks)
            if success:
                print("✅ Document processing complete!")
            else:
                print("❌ Failed to add chunks to Chroma!")
        else:
            print("❌ No documents processed!")
    
    def ask_question(self, question: str, include_sources: bool = True) -> str:
        """Ask a question and get an answer based on documents"""
        stats = self.embedding_manager.get_collection_stats()
        
        if stats['total_chunks'] == 0:
            return "❌ No documents loaded. Please add documents to the 'documents' folder."
        
        print(f"🔍 Searching for: {question}")
        
        # Find relevant chunks using Chroma
        relevant_chunks = self.embedding_manager.find_similar_chunks(
            question, 
            top_k=MAX_RELEVANT_CHUNKS
        )
        
        if not relevant_chunks:
            return self._fallback_answer(question)
        
        # Build context from relevant chunks
        context = self._build_context(relevant_chunks)
        
        # Generate answer using Ollama
        answer = self._generate_answer(question, context)
        
        # Add sources if requested
        if include_sources:
            sources = list(set(chunk['source'] for chunk in relevant_chunks))
            answer += f"\n\n📚 **Sources:** {', '.join(sources)}"
        
        return answer
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from relevant chunks"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"**Source {i} ({chunk['source']}):**\n{chunk['content']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Ollama"""
        system_prompt = """You are a helpful assistant that answers questions based on provided documents. 

IMPORTANT RULES:
- Only answer based on the provided context
- If the context doesn't contain enough information, say so clearly
- Be specific and cite relevant details from the context
- Maintain a helpful and professional tone"""

        user_prompt = f"""Question: {question}

Context from documents:
{context}

Please provide a comprehensive answer based on the context above."""

        try:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"❌ Error generating answer: {str(e)}"
    
    def _fallback_answer(self, question: str) -> str:
        """Fallback when no relevant chunks found"""
        try:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[{
                    'role': 'user',
                    'content': f"{question}\n\nNote: I don't have specific context for this question in the loaded documents."
                }]
            )
            return response['message']['content']
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return self.embedding_manager.get_collection_stats()
    
    def refresh_documents(self):
        """Refresh document processing (useful when adding new docs)"""
        print("🔄 Refreshing document processing...")
        
        # Clear existing collection
        self.embedding_manager.clear_collection()
        
        # Reprocess documents
        self._process_documents()

# Test the RAG system
if __name__ == "__main__":
    rag = RAGSystem()
    
    print("\n" + "="*50)
    print("🤖 RAG System Test")
    print("="*50)
    
    # Show stats
    stats = rag.get_system_stats()
    print(f"Status: {stats}")
    
    # Test question
    if stats['status'] == 'Ready':
        test_question = "What are the main topics covered in the documents?"
        answer = rag.ask_question(test_question)
        print(f"\nQ: {test_question}")
        print(f"A: {answer}")
    else:
        print("ℹ️ Add documents to the 'documents' folder to test the system")
EOF

# Create src/chat_interface.py
cat > src/chat_interface.py << 'EOF'
"""Interactive chat interface for the RAG system"""
import streamlit as st
from rag_system import RAGSystem
import time

# Page configuration
st.set_page_config(
    page_title="🤖 Intelligent Document Assistant",
    page_icon="📚",
    layout="wide"
)

# Initialize RAG system
@st.cache_resource
def load_rag_system():
    return RAGSystem()

def main():
    st.title("🤖 Intelligent Document Assistant")
    st.markdown("*Powered by Docling + Ollama + phi3:mini*")
    
    # Load system
    try:
        rag = load_rag_system()
        stats = rag.get_system_stats()
    except Exception as e:
        st.error(f"❌ Error loading system: {e}")
        st.stop()
    
    # Sidebar with system info
    with st.sidebar:
        st.header("📊 System Status")
        
        if stats['status'] == 'Ready':
            st.success("✅ System Ready")
            st.metric("Documents", stats['unique_sources'])
            st.metric("Knowledge Chunks", stats['total_chunks'])
            
            with st.expander("📚 Loaded Documents"):
                for doc in stats['sources']:
                    st.write(f"• {doc}")
        else:
            st.warning("⚠️ No documents loaded")
            st.info("Add PDF/DOCX/TXT files to the 'documents' folder and restart")
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh Documents"):
            with st.spinner("Processing documents..."):
                rag.refresh_documents()
            st.rerun()
    
    # Main chat interface
    if stats['status'] != 'Ready':
        st.warning("⚠️ Please add documents to get started!")
        st.info("1. Add PDF/DOCX/TXT files to the 'documents' folder\n2. Click 'Refresh Documents'")
        return
    
    # Chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your document assistant. Ask me anything about your uploaded documents."}
        ]
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                response = rag.ask_question(prompt, include_sources=True)
            st.write(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
EOF

echo "✅ All source files created successfully!"
echo ""
echo "📁 Created files:"
echo "  • src/document_processor.py"
echo "  • src/embedding_manager.py" 
echo "  • src/rag_system.py"
echo "  • src/chat_interface.py"
echo ""
echo "🚀 Now you can run:"
echo "  • Test: uv run python test_setup.py"
echo "  • Launch: ./run.sh"