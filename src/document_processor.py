"""Document processing using Docling"""
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from docling.document_converter import DocumentConverter
from docling.datamodel.document import ConversionResult
from config.settings import DOCUMENTS_DIR, CHUNKS_DIR

class DoclingProcessor:
    """High-quality document processing using Docling"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.converter = DocumentConverter()
        print("✅ Docling processor initialized")
    
    def process_document(self, file_path: Path, doc_index: int = None, total_docs: int = None) -> Dict:
        """Process a single document with Docling"""
        print(f"📄 Processing: {file_path.name}")
        
        # Update progress if callback is provided
        if self.progress_callback and doc_index is not None and total_docs is not None:
            self.progress_callback(
                f"Extracting text from {file_path.name}", 
                doc_index, 
                total_docs, 
                f"extracting_text_{doc_index}"
            )
            
            # Additional UI update to show we're starting processing
            import time
            for status in ["Starting", "Reading file", "Extracting content"]:
                self.progress_callback(
                    f"{status} - {file_path.name}", 
                    doc_index, 
                    total_docs, 
                    f"extracting_text_{doc_index}"
                )
                time.sleep(0.5)  # Brief delay for UI to update
        
        try:
            # Update progress before potentially time-consuming operation
            if self.progress_callback and doc_index is not None and total_docs is not None:
                self.progress_callback(
                    f"Converting document - {file_path.name} (this may take a minute for large PDFs)", 
                    doc_index, 
                    total_docs, 
                    f"extracting_text_{doc_index}"
                )
            
            # Convert document using Docling
            result: ConversionResult = self.converter.convert(str(file_path))
            
            # Update progress after conversion
            if self.progress_callback and doc_index is not None and total_docs is not None:
                self.progress_callback(
                    f"Formatting content - {file_path.name}", 
                    doc_index, 
                    total_docs, 
                    f"extracting_text_{doc_index}"
                )
            
            # Extract structured content
            document_data = {
                'filename': file_path.name,
                'path': str(file_path),
                'content': result.document.export_to_markdown(),
                'metadata': {
                    'pages': getattr(result.document, 'page_count', 1),
                    'elements': len(getattr(result.document, 'texts', [])),
                    'tables': len(getattr(result.document, 'tables', [])),
                }
            }
            
            # Report completion
            if self.progress_callback and doc_index is not None and total_docs is not None:
                self.progress_callback(
                    f"✅ Completed {file_path.name} - {len(document_data['content'])} characters extracted", 
                    doc_index + 1,  # Increment to show progress
                    total_docs, 
                    f"extracted_text_{doc_index}"
                )
            
            print(f"  ✅ Extracted {len(document_data['content'])} characters")
            return document_data
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            if self.progress_callback and doc_index is not None and total_docs is not None:
                self.progress_callback(
                    f"❌ Error processing {file_path.name}: {str(e)}", 
                    doc_index, 
                    total_docs, 
                    "error"
                )
            return None
    
    def create_chunks(self, document_data: Dict, chunk_size: int = 1000, overlap: int = 200, 
                    doc_index: int = None, total_docs: int = None) -> List[Dict]:
        """Split document into overlapping chunks"""
        content = document_data['content']
        filename = document_data['filename']
        
        # Update progress if callback is provided
        if self.progress_callback and doc_index is not None and total_docs is not None:
            self.progress_callback(
                f"Creating chunks for {filename}",
                doc_index,
                total_docs,
                f"chunking_{doc_index}"
            )
        
        # Simple sentence-aware chunking
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        
        # Update on chunk progress periodically
        total_sentences = len(sentences)
        update_interval = max(1, total_sentences // 5)  # Update 5 times during chunking
        
        for i, sentence in enumerate(sentences):
            # Periodically update progress
            if self.progress_callback and doc_index is not None and total_docs is not None and i % update_interval == 0:
                percent = int((i / total_sentences) * 100)
                self.progress_callback(
                    f"Chunking {filename} - {percent}% complete ({i}/{total_sentences} sentences)",
                    doc_index,
                    total_docs,
                    f"chunking_{doc_index}_{i}"
                )
            
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
        
        # Final progress update for chunking
        if self.progress_callback and doc_index is not None and total_docs is not None:
            self.progress_callback(
                f"✅ Created {len(chunks)} chunks for {filename}",
                doc_index,
                total_docs,
                f"chunking_complete_{doc_index}"
            )
        
        print(f"  📑 Created {len(chunks)} chunks")
        return chunks
    
    def process_all_documents(self) -> List[Dict]:
        """Process all documents in the documents directory"""
        all_chunks = []
        supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.html'}
        
        print(f"🔍 Scanning {DOCUMENTS_DIR} for documents...")
        
        # Update progress if callback is provided
        if self.progress_callback:
            self.progress_callback("Scanning for documents...", 0, 1, "scanning")
        
        document_files = [
            f for f in DOCUMENTS_DIR.rglob('*') 
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not document_files:
            print("❌ No supported documents found!")
            print(f"   Supported formats: {', '.join(supported_extensions)}")
            if self.progress_callback:
                self.progress_callback("No documents found", 0, 1, "no_documents")
            return []
        
        print(f"📚 Found {len(document_files)} documents to process")
        if self.progress_callback:
            self.progress_callback(f"Found {len(document_files)} documents to process", 0, len(document_files), "found_docs")
        
        total_docs = len(document_files)
        for i, file_path in enumerate(document_files):
            # Pass progress information to process_document
            document_data = self.process_document(file_path, i, total_docs)
            if document_data:
                # Pass progress information to create_chunks
                chunks = self.create_chunks(document_data, doc_index=i, total_docs=total_docs)
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