"""Enhanced RAG system with smart incremental processing"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import ollama
from document_processor import DoclingProcessor
from embedding_manager import EmbeddingManager
from config.settings import LLM_MODEL, MAX_RELEVANT_CHUNKS

class SmartRAGSystem:
    """RAG system with intelligent incremental document processing"""
    
    def __init__(self, progress_callback: Optional[Callable] = None, auto_load: bool = False):
        self.progress_callback = progress_callback
        self.processor = DoclingProcessor(progress_callback=progress_callback)
        self.embedding_manager = EmbeddingManager(progress_callback=progress_callback)
        
        print("🚀 Smart RAG System initialized")
        
        # Only load documents automatically if specified
        if auto_load:
            self._load_or_process_documents()
        else:
            print("ℹ️ Document loading deferred - use refresh to process documents")
    
    def _update_progress(self, message: str, current: int = 0, total: int = 0, step: str = ""):
        """Update progress if callback is provided"""
        if self.progress_callback:
            self.progress_callback(message, current, total, step)
    
    def _get_existing_documents(self) -> Dict[str, Dict]:
        """Get list of documents already processed in ChromaDB"""
        try:
            # Get all documents from collection
            collection_data = self.embedding_manager.collection.get()
            
            existing_docs = {}
            if collection_data['metadatas']:
                for metadata in collection_data['metadatas']:
                    source = metadata.get('source', '')
                    if source and source not in existing_docs:
                        existing_docs[source] = {
                            'chunks_count': 0,
                            'last_modified': metadata.get('last_modified', 'unknown')
                        }
                    if source:
                        existing_docs[source]['chunks_count'] += 1
            
            return existing_docs
        except Exception as e:
            print(f"⚠️ Could not get existing documents: {e}")
            return {}
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """Get file modification time and size"""
        try:
            stat = file_path.stat()
            return {
                'modified_time': str(stat.st_mtime),
                'size': stat.st_size,
                'path': str(file_path)
            }
        except Exception:
            return {'modified_time': 'unknown', 'size': 0, 'path': str(file_path)}
    
    def _find_documents_to_process(self) -> tuple[List[Path], Dict[str, str]]:
        """Find which documents need processing (new or modified)"""
        supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.html'}
        documents_dir = Path("documents")
        
        # Get all document files
        all_files = [
            f for f in documents_dir.rglob('*') 
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not all_files:
            return [], {}
        
        # Get existing documents from ChromaDB
        existing_docs = self._get_existing_documents()
        
        files_to_process = []
        processing_reasons = {}
        
        for file_path in all_files:
            filename = file_path.name
            file_info = self._get_file_info(file_path)
            
            if filename not in existing_docs:
                # New file
                files_to_process.append(file_path)
                processing_reasons[filename] = "New file"
            else:
                # Check if file was modified
                existing_modified = existing_docs[filename].get('last_modified', 'unknown')
                current_modified = file_info['modified_time']
                
                if existing_modified != current_modified:
                    # File was modified
                    files_to_process.append(file_path)
                    processing_reasons[filename] = "Modified file"
                # else: File unchanged, skip processing
        
        return files_to_process, processing_reasons
    
    def _remove_old_chunks(self, filename: str):
        """Remove chunks for a specific file that's being reprocessed"""
        try:
            # Query for chunks from this file
            existing_chunks = self.embedding_manager.collection.get(
                where={"source": filename}
            )
            
            if existing_chunks['ids']:
                self.embedding_manager.collection.delete(ids=existing_chunks['ids'])
                print(f"🗑️ Removed {len(existing_chunks['ids'])} old chunks for {filename}")
        except Exception as e:
            print(f"⚠️ Could not remove old chunks for {filename}: {e}")
    
    def smart_refresh_documents(self, progress_callback: Optional[Callable] = None):
        """Smart document refresh - only processes new/modified files"""
        print("🧠 Starting smart document refresh...")
        
        # Update progress callback if provided
        if progress_callback:
            self.progress_callback = progress_callback
            self.processor.progress_callback = progress_callback
            self.embedding_manager.progress_callback = progress_callback
        
        self._update_progress("Analyzing documents for changes...", 0, 1, "analyzing")
        
        # Find documents that need processing
        files_to_process, reasons = self._find_documents_to_process()
        
        if not files_to_process:
            self._update_progress("✅ All documents are up to date!", 1, 1, "up_to_date")
            print("✅ All documents are up to date - no processing needed!")
            return
        
        total_files = len(files_to_process)
        self._update_progress(f"Found {total_files} files to process", 0, total_files, "found_changes")
        
        # Show what will be processed
        print(f"📋 Processing {total_files} files:")
        for file_path in files_to_process:
            reason = reasons.get(file_path.name, "Unknown")
            print(f"  • {file_path.name} ({reason})")
        
        # Process each file
        new_chunks = []
        for i, file_path in enumerate(files_to_process):
            filename = file_path.name
            reason = reasons.get(filename, "Unknown")
            
            self._update_progress(f"Processing {filename} ({reason})", i, total_files, "processing_file")
            
            # If file was modified, remove old chunks first
            if reason == "Modified file":
                self._remove_old_chunks(filename)
            
            # Process the document
            document_data = self.processor.process_document(file_path, i, total_files)
            if document_data:
                # Add file modification time to metadata
                document_data['metadata']['last_modified'] = self._get_file_info(file_path)['modified_time']
                
                # Create chunks
                chunks = self.processor.create_chunks(document_data, doc_index=i, total_docs=total_files)
                new_chunks.extend(chunks)
        
        # Add new chunks to ChromaDB
        if new_chunks:
            self._update_progress("Adding new chunks to database...", 0, 1, "adding_chunks")
            success = self.embedding_manager.add_chunks(new_chunks)
            
            if success:
                self._update_progress(f"✅ Successfully processed {total_files} files!", total_files, total_files, "smart_refresh_complete")
                print(f"✅ Smart refresh complete! Added {len(new_chunks)} new chunks")
            else:
                self._update_progress("❌ Failed to add chunks to database", 0, total_files, "error")
        else:
            self._update_progress("⚠️ No chunks generated from processed files", 0, total_files, "no_chunks")
    
    def force_full_refresh(self):
        """Force complete reprocessing of all documents"""
        print("🔄 Force full refresh - reprocessing all documents...")
        
        self._update_progress("Clearing all existing data...", 0, 1, "force_refresh_start")
        
        # Clear existing collection
        self.embedding_manager.clear_collection()
        
        # Reprocess all documents
        self._process_documents()
    
    def refresh_documents(self, progress_callback: Optional[Callable] = None):
        """Full document refresh - reprocesses all documents (alias for force_full_refresh)"""
        print("🔄 Starting full document refresh...")
        
        # Update progress callback if provided
        if progress_callback:
            self.progress_callback = progress_callback
            self.processor.progress_callback = progress_callback
            self.embedding_manager.progress_callback = progress_callback
        
        self._update_progress("Starting full document refresh...", 0, 1, "full_refresh_start")
        
        # Call force_full_refresh to do the actual work
        self.force_full_refresh()
        
        self._update_progress("✅ Full document refresh completed!", 1, 1, "full_refresh_complete")
        
    def get_system_status(self):
        """Get system status without loading or processing documents"""
        stats = self.embedding_manager.get_collection_stats()
        
        # Check if documents folder exists and contains documents
        document_files = self._get_document_files()
        
        status_data = {
            'status': 'Ready' if stats['total_chunks'] > 0 else 'No documents loaded',
            'total_chunks': stats['total_chunks'],
            'unique_sources': stats['unique_sources'],
            'sources': stats['sources'],
            'available_files': len(document_files),
            'pending_updates': 0,
            'update_reasons': {}
        }
        
        # Check for pending updates only if we have documents
        if stats['total_chunks'] > 0:
            files_to_process, reasons = self._find_documents_to_process()
            status_data['pending_updates'] = len(files_to_process)
            status_data['update_reasons'] = reasons
        
        return status_data
    
    def _get_document_files(self):
        """Get list of document files in the documents directory"""
        supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.html'}
        documents_dir = Path("documents")
        
        # Get all document files
        return [
            f for f in documents_dir.rglob('*') 
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
    
    def _load_or_process_documents(self):
        """Load existing embeddings or process documents"""
        # Check if we have documents in Chroma
        stats = self.embedding_manager.get_collection_stats()
        
        if stats['total_chunks'] > 0:
            print(f"📚 Found existing collection with {stats['total_chunks']} chunks")
            self._update_progress(f"Found existing collection with {stats['total_chunks']} chunks", 1, 1, "existing_collection")
            return
        
        print("📚 No existing collection found. Processing documents...")
        self._update_progress("No existing collection found. Processing documents...", 0, 1, "need_processing")
        self._process_documents()
    
    def _process_documents(self):
        """Process all documents and add to Chroma with progress tracking"""
        self._update_progress("Starting document processing...", 0, 1, "start_processing")
        
        # Process documents with Docling
        chunks = self.processor.process_all_documents()
        
        if chunks:
            # Add file modification times to metadata
            for chunk in chunks:
                file_path = Path("documents") / chunk['source']
                if file_path.exists():
                    chunk['metadata']['last_modified'] = self._get_file_info(file_path)['modified_time']
            
            # Add to Chroma (handles embedding generation automatically)
            self._update_progress("Adding chunks to vector database...", 0, 1, "adding_to_db")
            success = self.embedding_manager.add_chunks(chunks)
            if success:
                print("✅ Document processing complete!")
                self._update_progress("✅ Document processing completed successfully!", 1, 1, "processing_complete")
            else:
                print("❌ Failed to add chunks to Chroma!")
                self._update_progress("❌ Failed to add chunks to vector database", 0, 1, "processing_failed")
        else:
            print("❌ No documents processed!")
            self._update_progress("❌ No documents found to process", 0, 1, "no_documents")
    
    # Keep all other methods from original RAGSystem
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
        # Use our new system status method for consistency
        return self.get_system_status()

# Backward compatibility - alias to new smart system
RAGSystem = SmartRAGSystem