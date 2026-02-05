import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.rag_engine import RAGEngine


def initialize_rag():
    """Initialize RAG engine"""
    if 'rag_engine' not in st.session_state:
        with st.spinner("🚀 Initializing RAG system..."):
            try:
                st.session_state.rag_engine = RAGEngine()
                st.session_state.rag_initialized = True
                st.success("✅ RAG system ready!")
            except Exception as e:
                st.error(f"❌ Failed to initialize RAG: {e}")
                st.session_state.rag_initialized = False
    
    return st.session_state.get('rag_initialized', False)


def display_sources(sources):
    """Display sources with relevance"""
    if not sources:
        return
    
    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for source in sources:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.text(f"[{source['id']}] {source['source']}")
            with col2:
                st.text(source['type'])
            with col3:
                st.metric("Match", source['relevance'])


def main():
    st.set_page_config(
        page_title="RAG Chat - STIX Intelligence",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 STIX Intelligence RAG Chat")
    st.markdown("Ask questions about STIX formats, MITRE ATT&CK, threat intelligence, and more!")
    
    # Initialize RAG
    if not initialize_rag():
        st.error("❌ RAG system failed to initialize")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ System Control")
        
        if st.button("🔄 Rebuild Index", use_container_width=True):
            with st.spinner("Rebuilding index..."):
                try:
                    st.session_state.rag_engine.build_index()
                    st.success("✅ Index rebuilt!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.divider()
        
        # System stats
        try:
            stats = st.session_state.rag_engine.get_stats()
            doc_count = stats['vector_store_info']['document_count']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Documents", doc_count)
            with col2:
                st.metric("🔌 Model", stats['model_name'].split(':')[0])
            
            # Test connection
            if st.button("🧪 Test Ollama", use_container_width=True):
                with st.spinner("Testing..."):
                    if st.session_state.rag_engine.test_connection():
                        st.success("✅ Ollama connected!")
                    else:
                        st.error("❌ Ollama not responding")
        
        except Exception as e:
            st.error(f"Stats error: {e}")
        
        st.divider()
        st.markdown("""
        ### 💡 Example Questions:
        - What is a STIX indicator?
        - Explain MITRE ATT&CK
        - STIX 2.0 vs 2.1 differences?
        - Malware attack patterns?
        """)
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                display_sources(message["sources"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_engine.query(prompt)
                    
                    st.markdown(response['answer'])
                    
                    # Show sources
                    if response.get('sources'):
                        display_sources(response['sources'])
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response['answer'],
                        "sources": response.get('sources', [])
                    })
                
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Clear chat button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
