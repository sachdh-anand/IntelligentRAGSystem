import sys
import os
sys.path.append(".")

try:
    import ollama
    import chromadb  
    import docling
    print("✅ All imports successful!")
    
    # Test Ollama connection
    models = ollama.list()
    print("✅ Ollama connected")
    
    # Test a simple question
    response = ollama.chat(
        model="phi3:mini",
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("✅ phi3:mini working!")
    print("🎉 System is ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")