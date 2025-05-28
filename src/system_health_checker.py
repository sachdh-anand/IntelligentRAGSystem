import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import ollama
import time
from config.settings import LLM_MODEL, EMBEDDING_MODEL

class SystemHealthChecker:
    def __init__(self):
        self.required_models = [LLM_MODEL, EMBEDDING_MODEL]
    
    def check_ollama_service(self) -> bool:
        try:
            ollama.list()
            print("✅ Ollama service is running")
            return True
        except Exception as e:
            print(f"❌ Ollama service not available: {e}")
            return False
    
    def check_models(self) -> dict:
        try:
            models_response = ollama.list()
            available_models = []
            
            # Handle different response structures
            if isinstance(models_response, dict) and 'models' in models_response:
                for model in models_response['models']:
                    if isinstance(model, dict) and 'name' in model:
                        available_models.append(model['name'])
                    elif isinstance(model, str):
                        available_models.append(model)
            
            status = {}
            for model in self.required_models:
                status[model] = model in available_models
                if status[model]:
                    print(f"✅ {model} is available")
                else:
                    print(f"❌ {model} is missing")
            
            return status
        except Exception as e:
            print(f"❌ Error checking models: {e}")
            return {model: False for model in self.required_models}
    
    def quick_check(self) -> bool:
        try:
            # Test actual functionality instead of parsing
            ollama.chat(model=LLM_MODEL, messages=[{'role': 'user', 'content': 'test'}])
            ollama.embeddings(model=EMBEDDING_MODEL, prompt='test')
            return True
        except:
            return False
    
    def full_health_check(self) -> bool:
        print("🔍 Performing system health check...")
        
        if not self.check_ollama_service():
            return False
        
        # Simple functional test
        try:
            print("Testing phi3:mini...")
            ollama.chat(model='phi3:mini', messages=[{'role': 'user', 'content': 'test'}])
            print("✅ phi3:mini working")
            
            print("Testing nomic-embed-text...")
            ollama.embeddings(model='nomic-embed-text', prompt='test')
            print("✅ nomic-embed-text working")
            
            print("✅ All models functional!")
            return True
            
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False

def main():
    checker = SystemHealthChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        if checker.quick_check():
            print("✅ System is healthy")
            sys.exit(0)
        else:
            print("❌ System needs attention")
            sys.exit(1)
    else:
        if checker.full_health_check():
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()