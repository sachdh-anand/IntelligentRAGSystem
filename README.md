# 🤖 Intelligent Document Assistant

A production-grade, smart RAG (Retrieval-Augmented Generation) system that lets you chat with your documents using advanced AI techniques.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-red.svg)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-0.4.8+-green.svg)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🔍 Overview

The Intelligent Document Assistant transforms static documents (PDFs, Word files, text) into an interactive knowledge base you can chat with. It features:

- **Smart Document Processing**: Only processes new or modified files, saving time and resources
- **Professional Chat Interface**: Clean Streamlit UI with real-time progress tracking
- **High-Quality Document Understanding**: Uses Docling for superior text extraction from PDFs and DOCXs
- **Local Privacy**: All processing happens on your machine with Ollama - no data leaves your system
- **Source Citations**: Every answer includes references to the source documents
- **Intelligent Chunking**: Advanced document segmentation for better context understanding

## 🌟 Key Features

### 🧠 Smart Incremental Processing

Unlike most RAG systems that reprocess all documents for every change, this system:
- ✅ Detects new or modified files automatically
- ✅ Only processes documents that have changed
- ✅ Maintains a persistent vector database
- ✅ Tracks document versions and modifications
- ✅ Visualizes processing status with detailed progress indicators

### 💬 Professional Chat Experience

- **Interactive Interface**: Clean, modern Streamlit UI
- **Real-time Feedback**: Visual processing indicators with time estimates
- **Source Citations**: Every answer includes document references
- **System Health Monitoring**: Complete visibility into model and service status
- **Performance Metrics**: Track processing and response times

### 🔧 Technical Stack

- **LLM**: [phi3:mini](https://ollama.com/library/phi3) via Ollama for efficient local text generation
- **Embeddings**: [nomic-embed-text](https://ollama.com/library/nomic-embed-text) for high-quality document embeddings
- **Vector Database**: ChromaDB for persistent storage and efficient similarity search
- **Document Processing**: Docling for superior document text extraction
- **UI Framework**: Streamlit for interactive web interface
- **Language**: Python 3.12+

## 📁 Project Structure

```
intelligent-rag-system/
├── 🧠 Core Intelligence
│   ├── src/rag_system.py          # Smart RAG orchestration with incremental processing
│   ├── src/document_processor.py  # Docling-powered document extraction
│   └── src/embedding_manager.py   # ChromaDB vector operations & management
├── 🎨 User Interface  
│   └── src/chat_interface.py      # Professional Streamlit chat interface
├── ⚙️ Configuration
│   └── config/settings.py         # Centralized system configuration
├── 📚 Data Pipeline
│   ├── documents/                 # Input documents (PDF, DOCX, TXT, MD)
│   └── processed/                 # Vector database & processed chunks
└── 🚀 Deployment
    ├── run.ps1                    # Windows PowerShell startup script
    └── run.sh                     # Unix/Linux startup script
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** ([Download here](https://www.python.org/downloads/))
- **Ollama** ([Install guide](https://ollama.com/download))
- **uv** package manager (recommended): `pip install uv`

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/intelligent-rag-system.git
   cd intelligent-rag-system
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Install required Ollama models**
   ```bash
   ollama pull phi3:mini
   ollama pull nomic-embed-text
   ```

4. **Add your documents**
   - Place PDF, DOCX, TXT, or MD files in the `documents/` folder

5. **Start the system**

   **Windows:**
   ```powershell
   .\run.ps1
   ```
   
   **Unix/Linux:**
   ```bash
   ./run.sh
   ```

6. **Open your browser**
   - Navigate to `http://localhost:8501`
   - Start chatting with your documents!

## 💡 Usage Examples

### Basic Chat
```
You: "What are the main topics covered in my documents?"
Assistant: "Based on your documents, the main topics include... [Sources: document1.pdf, document2.docx]"
```

### Smart Processing
- **First run**: Processes all documents in `documents/` folder
- **Subsequent runs**: Only processes new or modified files
- **Real-time feedback**: Progress bars show extraction and embedding progress

## 🏗️ Architecture

```mermaid
graph TD
    A[Documents Folder] --> B[Document Processor]
    B --> C[Intelligent Chunking]
    C --> D[Embedding Manager]
    D --> E[ChromaDB Vector Store]
    F[User Query] --> G[RAG System]
    G --> E
    E --> H[Relevant Chunks]
    H --> I[Context Building]
    I --> J[Ollama LLM]
    J --> K[Generated Answer + Sources]
```

**Key Components:**
- **Smart Document Processing**: Incremental updates using file modification tracking
- **Vector Embeddings**: High-quality nomic-embed-text embeddings via Ollama
- **Retrieval System**: ChromaDB similarity search with configurable relevance thresholds
- **Generation**: Local phi3:mini model for privacy-focused AI responses

## 🎯 Key Innovations

### 1. **Incremental Processing Intelligence**
Most RAG systems reprocess everything on each run. Our system:
- Tracks file modification timestamps
- Only processes new/changed documents
- Maintains vector database consistency
- Provides 10x faster startup for large document collections

### 2. **Production-Ready Features**
- Comprehensive health monitoring
- Automatic Ollama service management
- Professional error handling and recovery
- Real-time progress tracking with detailed feedback

### 3. **Privacy-First Design**
- 100% local processing with Ollama
- No external API calls or data transmission
- Your documents never leave your machine

## 📊 Performance

- **Processing Speed**: ~1-2 seconds per document page
- **Memory Usage**: ~200MB baseline + ~50MB per 1000 chunks
- **Storage**: ~1KB per document chunk in vector database
- **Query Response**: ~2-5 seconds for complex questions

## 🛠️ Configuration

Edit `config/settings.py` to customize:

```python
# Model settings
LLM_MODEL = "phi3:mini"           # Or "llama3.2", "qwen2.5", etc.
EMBEDDING_MODEL = "nomic-embed-text"

# Processing settings
CHUNK_SIZE = 1000                 # Characters per chunk
CHUNK_OVERLAP = 200              # Overlap between chunks
MAX_RELEVANT_CHUNKS = 5          # Chunks used for context
```

## 🧪 Testing

Run the test suite:
```bash
uv run python -m pytest tests/
```

Simple health check:
```bash
uv run python tests/test_simple.py
```

## 🚧 Roadmap

- [ ] **Hybrid Search**: Combine semantic + keyword search
- [ ] **Multi-language Support**: Expand beyond English documents
- [ ] **Advanced Chunking**: Document-aware segmentation
- [ ] **Query Analytics**: Track common questions and optimize retrieval
- [ ] **API Mode**: REST API for integration with other systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Docling](https://github.com/DS4SD/docling)** for superior document processing
- **[Ollama](https://ollama.com)** for local LLM hosting
- **[ChromaDB](https://www.trychroma.com/)** for vector database capabilities
- **[Streamlit](https://streamlit.io)** for rapid UI development

## 💬 Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/yourusername/intelligent-rag-system/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/yourusername/intelligent-rag-system/discussions)

---

*Built with ❤️ for the AI community. Star ⭐ this repo if it helped you build better RAG systems!*
