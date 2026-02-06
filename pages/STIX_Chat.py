import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.rag_engine import RAGEngine

def initialize_rag():
    """Initialize RAG engine"""
    if 'rag_engine' not in st.session_state:
        with st.spinner("Initializing RAG system..."):
            try:
                st.session_state.rag_engine = RAGEngine()
                st.session_state.rag_initialized = True
            except Exception as e:
                st.error(f"Failed to initialize RAG: {e}")
                st.session_state.rag_initialized = False
    
    return st.session_state.get('rag_initialized', False)

def display_sources(sources):
    """Display source information"""
    if sources:
        with st.expander("📚 Sources Used", expanded=False):
            for i, source in enumerate(sources, 1):
                st.markdown(f"""
                **Source {i}:**
                - File: `{source['source']}`
                - Type: `{source['type']}`
                - STIX Type: `{source.get('stix_type', 'N/A')}`
                - Relevance: {source['relevance']}
                """)

def main():
    st.title("🤖 STIX Intelligence RAG Chat")
    st.markdown("Ask questions about STIX formats, MITRE ATT&CK, threat intelligence, and more!")
    
    # Initialize RAG
    if not initialize_rag():
        st.error("❌ RAG system failed to initialize. Please check the logs.")
        return
    
    # Sidebar with system info
    with st.sidebar:
        st.header("⚙️ System Info")
        
        if st.button("🔄 Rebuild Index"):
            with st.spinner("Rebuilding index..."):
                try:
                    st.session_state.rag_engine.build_index()
                    st.success("Index rebuilt successfully!")
                except Exception as e:
                    st.error(f"Error rebuilding index: {e}")
        
        # Display stats
        try:
            stats = st.session_state.rag_engine.get_stats()
            st.metric("Documents Indexed", stats['vector_store_info']['document_count'])
            st.info(f"**Model:** {stats['model_name']}")
            
            # Test Ollama connection
            if st.button("🔌 Test Ollama Connection"):
                with st.spinner("Testing connection..."):
                    if st.session_state.rag_engine.test_connection():
                        st.success("✅ Ollama connected!")
                    else:
                        st.error("❌ Ollama not responding")
        except Exception as e:
            st.error(f"Error getting stats: {e}")
        
        st.divider()
        st.markdown("""
        ### 💡 Example Questions:
        - What is a STIX indicator?
        - Explain MITRE ATT&CK technique T1566
        - How do I convert STIX 1.x to 2.1?
        - What malware uses spearphishing?
        - Difference between STIX 2.0 and 2.1?
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
    if prompt := st.chat_input("Ask me anything about STIX or threat intelligence..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_engine.query(prompt)
                    
                    # Display answer
                    st.markdown(response['answer'])
                    
                    # Display sources
                    if response.get('sources'):
                        display_sources(response['sources'])
                    
                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response['answer'],
                        "sources": response.get('sources', [])
                    })
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()