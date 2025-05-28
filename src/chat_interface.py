"""Smart chat interface with incremental document processing"""
import streamlit as st
import ollama
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag_system import RAGSystem  # Use existing system
from config.settings import LLM_MODEL, EMBEDDING_MODEL

# Page configuration
st.set_page_config(
    page_title="🤖 Intelligent Document Assistant",
    page_icon="📚",
    layout="wide"
)

@st.cache_data(ttl=30)  # Cache for 30 seconds
def check_ollama_status():
    """Check Ollama service and model status"""
    try:
        # Check if Ollama service is running
        models_response = ollama.list()
        
        # Extract model names from Ollama response
        # Ollama API returns a ListResponse object with models attribute
        model_names = []
        if hasattr(models_response, 'models'):
            for model in models_response.models:
                # Use 'model' attribute which is the standard field in Ollama API
                if hasattr(model, 'model'):
                    model_names.append(model.model)
        
        # Debug info - can be removed later
        print(f"Detected models: {model_names}")
        
        # Accept both with and without :latest tag
        def matches_model(name, required):
            return name == required or name == f"{required}:latest" or name.split(':')[0] == required
        
        llm_available = any(matches_model(name, LLM_MODEL) for name in model_names)
        embedding_available = any(matches_model(name, EMBEDDING_MODEL) for name in model_names)
        
        # Get model details
        model_details = {}
        if hasattr(models_response, 'models'):
            for model in models_response.models:
                if hasattr(model, 'model'):
                    model_name = model.model
                    if matches_model(model_name, LLM_MODEL) or matches_model(model_name, EMBEDDING_MODEL):
                        model_details[model_name] = {
                            'size': getattr(model, 'size', 'Unknown'),
                            'modified': getattr(model, 'modified_at', 'Unknown'),
                            'digest': getattr(model, 'digest', '')[:12] + '...' if getattr(model, 'digest', '') else ''
                        }
        
        return {
            'service_running': True,
            'llm_available': llm_available,
            'embedding_available': embedding_available,
            'total_models': len(model_names),
            'model_details': model_details,
            'all_models': model_names
        }
        
    except Exception as e:
        return {
            'service_running': False,
            'error': str(e),
            'llm_available': False,
            'embedding_available': False
        }

def format_size(size_bytes):
    """Format bytes to human readable size"""
    if size_bytes == 'Unknown':
        return 'Unknown'
    
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except Exception:
        return str(size_bytes)

# Initialize RAG system
@st.cache_resource
def load_rag_system():
    # Initialize with a dummy progress callback to prevent UI blocking
    def dummy_progress(message, current, total, step):
        # This prevents long operations from blocking the UI
        # The real progress updates will happen during explicit refresh operations
        print(f"Background init: {message} ({current}/{total}) - {step}")
    
    # Set auto_load=False to prevent automatic document loading on startup
    return RAGSystem(progress_callback=dummy_progress, auto_load=False)

def main():
    st.title("🤖 Intelligent Document Assistant")
    st.markdown("*Powered by Docling + Ollama + phi3:mini with Smart Processing*")
    
    # Check Ollama status first
    ollama_status = check_ollama_status()
    
    # Sidebar with system info
    with st.sidebar:
        st.header("🔧 Ollama Status")
        
        if ollama_status['service_running']:
            st.success("✅ Ollama Service Running")
            
            # Model status
            col1, col2 = st.columns(2)
            with col1:
                if ollama_status['llm_available']:
                    st.success(f"✅ {LLM_MODEL}")
                else:
                    st.error(f"❌ {LLM_MODEL}")
            
            with col2:
                if ollama_status['embedding_available']:
                    st.success(f"✅ {EMBEDDING_MODEL}")
                else:
                    st.error(f"❌ {EMBEDDING_MODEL}")
            
            # Model details
            if ollama_status.get('model_details'):
                with st.expander("📋 Model Details"):
                    for model_name, details in ollama_status['model_details'].items():
                        st.write(f"**{model_name}**")
                        st.write(f"• Size: {format_size(details['size'])}")
                        st.write(f"• Modified: {details['modified']}")
                        if details['digest']:
                            st.write(f"• ID: {details['digest']}")
                        st.write("---")
            
            st.metric("Total Models", ollama_status.get('total_models', 0))
            
        else:
            st.error("❌ Ollama Service Offline")
            if ollama_status.get('error'):
                st.warning(f"Ollama error: {ollama_status['error']}")
            st.info("Start with: `ollama serve`")
            if st.button("🔄 Retry Connection"):
                st.rerun()
        
        st.divider()
        
        # Document system status
        st.header("📊 System Status")
        
        # Load RAG system
        try:
            rag = load_rag_system()
            stats = rag.get_system_stats()
        except Exception as e:
            st.error(f"❌ Error loading system: {e}")
            st.stop()
        
        if stats['status'] == 'Ready':
            st.success("✅ System Ready")
            
            # Enhanced metrics with smart processing info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats['unique_sources'])
                st.metric("Knowledge Chunks", stats['total_chunks'])
            
            with col2:
                pending = stats.get('pending_updates', 0)
                if pending > 0:
                    st.metric("⚠️ Pending Updates", pending, delta=f"{pending} files")
                else:
                    st.metric("✅ Up to Date", "All files")
            
            # Show pending updates if any
            if stats.get('update_reasons'):
                with st.expander("⚠️ Files Needing Updates"):
                    for filename, reason in stats['update_reasons'].items():
                        st.write(f"• **{filename}** - {reason}")
            
            with st.expander("📚 Loaded Documents"):
                for doc in stats['sources']:
                    st.write(f"• {doc}")
        else:
            st.warning("⚠️ No documents loaded")
            st.info("Add PDF/DOCX/TXT files to the 'documents' folder")
        
        st.divider()
        
        # Smart control buttons
        st.header("🎛️ Document Control")
        
        # Smart vs Full refresh options
        refresh_type = st.radio(
            "Refresh Type:",
            ["🧠 Smart (Only New/Modified)", "🔄 Full (All Documents)"],
            help="Smart refresh only processes changed files. Full refresh reprocesses everything."
        )
        
        if st.button("🚀 Refresh Documents", type="primary"):
            # Create progress display
            progress_container = st.container()
            with progress_container:
                if "Smart" in refresh_type:
                    st.subheader("🧠 Smart Document Processing")
                    st.info("Only processing new or modified files...")
                else:
                    st.subheader("🔄 Full Document Processing")
                    st.warning("Reprocessing all documents...")
                
                # Progress tracking variables
                progress_bar = st.progress(0)
                status_text = st.empty()
                current_step = st.empty()
                detail_text = st.empty()
                time_estimate = st.empty()
                
                # Time tracking
                start_time = time.time()
                last_progress = 0
                
                # Step indicators
                step_cols = st.columns(5)
                step_indicators = []
                step_names = ["🔍 Analyze", "📄 Extract", "✂️ Chunk", "🧠 Embed", "✅ Done"]
                
                for i, (col, name) in enumerate(zip(step_cols, step_names)):
                    with col:
                        step_indicators.append(st.empty())
                        step_indicators[i].markdown(f"⚪ {name}")
                
                # Progress callback function
                def update_progress(message: str, current: int, total: int, step: str):
                    nonlocal last_progress, start_time
                    
                    # Update main progress
                    if total > 0:
                        progress = min(current / total, 1.0)
                        progress_bar.progress(progress)
                        status_text.text(f"Progress: {current}/{total} ({progress*100:.1f}%)")
                        
                        # Estimate time remaining
                        if progress > 0.1 and progress > last_progress:
                            elapsed = time.time() - start_time
                            estimated_total = elapsed / progress
                            remaining = estimated_total - elapsed
                            time_estimate.text(f"⏱️ Est. remaining: {remaining:.1f}s")
                        
                        last_progress = progress
                    
                    # Update current step
                    current_step.text(f"📋 {message}")
                    
                    # Update step indicators based on step type
                    if step.startswith('analyzing') or step == 'found_changes':
                        step_indicators[0].markdown("🟡 🔍 Analyze")
                        detail_text.text("🔍 Analyzing files for changes...")
                        
                    elif step == 'up_to_date':
                        for i in range(5):
                            step_indicators[i].markdown(f"🟢 {step_names[i]}")
                        detail_text.text("✅ All files are up to date!")
                        time_estimate.text("⏱️ No processing needed!")
                        
                    elif step.startswith('processing_file') or step.startswith('extracting_text'):
                        step_indicators[0].markdown("✅ 🔍 Analyze")
                        step_indicators[1].markdown("🟡 📄 Extract")
                        detail_text.text("📄 Extracting text from documents...")
                        
                    elif step.startswith('creating_chunks') or step.startswith('chunking'):
                        step_indicators[1].markdown("✅ 📄 Extract")
                        step_indicators[2].markdown("🟡 ✂️ Chunk")
                        detail_text.text("✂️ Creating intelligent chunks...")
                        
                    elif step.startswith('adding_chunks') or step.startswith('batch'):
                        step_indicators[2].markdown("✅ ✂️ Chunk")
                        step_indicators[3].markdown("🟡 🧠 Embed")
                        detail_text.text("🧠 Generating embeddings with AI...")
                        
                    elif step in ['smart_refresh_complete', 'processing_complete']:
                        for i in range(4):
                            step_indicators[i].markdown(f"✅ {step_names[i]}")
                        step_indicators[4].markdown("🟢 ✅ Done")
                        detail_text.text("🎉 Smart processing completed!")

                    elif step == "error":
                        detail_text.text("❌ Processing error occurred!")
                    
                    # Force Streamlit to update
                    time.sleep(0.1)
                
                # Perform the refresh with progress tracking
                try:
                    if "Smart" in refresh_type:
                        rag.smart_refresh_documents(progress_callback=update_progress)
                    else:
                        rag.refresh_documents(progress_callback=update_progress)
                    
                    # Final success state
                    progress_bar.progress(1.0)
                    status_text.text("✅ Complete!")
                    
                    # Show completion metrics
                    new_stats = rag.get_system_stats()
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Documents", new_stats['unique_sources'])
                    with col_b:
                        st.metric("Chunks", new_stats['total_chunks'])
                    with col_c:
                        processing_time = time.time() - start_time
                        st.metric("Time", f"{processing_time:.1f}s")
                    
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text(f"❌ Error: {str(e)}")
                    current_step.text("💥 Processing failed!")
                    detail_text.text(f"Please check your documents: {str(e)}")
        
        # Quick actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Check Status"):
                st.cache_resource.clear()
                st.rerun()
        
        with col2:
            if st.button("🔍 Check Models"):
                st.cache_data.clear()
                st.rerun()
    
    # Main chat interface
    if not (ollama_status['service_running'] and 
            ollama_status['llm_available'] and 
            ollama_status['embedding_available']):
        st.warning("⚠️ Please ensure Ollama service and models are available!")
        return
    
    if stats['status'] != 'Ready':
        st.warning("⚠️ Please add documents to get started!")
        st.info("1. Add PDF/DOCX/TXT files to the 'documents' folder\n2. Click 'Refresh Documents'")
        return
    
    # Performance metrics
    if st.checkbox("📊 Show Performance Info"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Response Model", LLM_MODEL)
        with col2:
            st.metric("Embedding Model", EMBEDDING_MODEL)
        with col3:
            st.metric("Vector DB", "ChromaDB")
        with col4:
            st.metric("Processing", "Smart Incremental")
    
    # Chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your intelligent document assistant with smart processing. I only update documents when they change, making everything faster! What would you like to know?"}
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
            with st.spinner("🧠 Analyzing documents and generating response..."):
                start_time = time.time()
                response = rag.ask_question(prompt, include_sources=True)
                response_time = time.time() - start_time
            
            st.write(response)
            
            # Show response time if performance info is enabled
            if st.session_state.get('show_perf', False):
                st.caption(f"⏱️ Response time: {response_time:.2f}s")
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
