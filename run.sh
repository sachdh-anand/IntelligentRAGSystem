#!/bin/bash
echo "🚀 Starting Intelligent RAG System..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Starting Ollama service..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 3
fi

# Launch the web interface
echo "🌐 Launching web interface..."
echo "Visit: http://localhost:8501"
uv run streamlit run src/chat_interface.py
