import ollama
from typing import List, Dict, Any, Optional
import logging
from .vector_store import VectorStoreManager
from .rag_processor import RAGDocumentProcessor

class RAGEngine:
    def __init__(self, knowledge_base_path: str = "knowledge_base", model_name: str = "llama3.1:8b"):
        self.knowledge_base_path = knowledge_base_path
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.processor = RAGDocumentProcessor(knowledge_base_path)
        self.vector_store = VectorStoreManager()
        
        # Check if index exists, if not build it
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure vector index exists, build if necessary"""
        info = self.vector_store.get_collection_info()
        if info['document_count'] == 0:
            self.logger.info("No documents in vector store, building index...")
            self.build_index()
    
    def build_index(self):
        """Build or rebuild the vector index"""
        self.logger.info("Processing documents from knowledge base...")
        documents = self.processor.process_all_documents()
        
        if documents:
            self.logger.info(f"Adding {len(documents)} documents to vector store...")
            self.vector_store.rebuild_index(documents)
            self.logger.info("Index built successfully")
        else:
            self.logger.warning("No documents found to index")
    
    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Process a query using RAG"""
        try:
            # Retrieve relevant documents
            self.logger.info(f"Searching for relevant documents for: {question}")
            retrieved_docs = self.vector_store.search(question, n_results)
            
            if not retrieved_docs:
                return {
                    "answer": "I couldn't find relevant information in the knowledge base.",
                    "sources": [],
                    "error": "No relevant documents found"
                }
            
            # Generate response
            response = self._generate_response(question, retrieved_docs)
            
            return {
                "answer": response,
                "sources": self._format_sources(retrieved_docs),
                "retrieved_docs": len(retrieved_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "error": str(e)
            }
    
    def _generate_response(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate response using Ollama"""
        # Build context from retrieved documents
        context = self._build_context(retrieved_docs)
        
        # Create prompt
        prompt = self._create_prompt(question, context)
        
        try:
            # Call Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc['metadata'].get('source', 'Unknown')
            doc_type = doc['metadata'].get('type', 'Unknown')
            content = doc['content'][:1000]  # Limit content length
            
            context_parts.append(f"Document {i} (Source: {source}, Type: {doc_type}):\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for the LLM"""
        return f"""You are a cybersecurity expert specializing in STIX threat intelligence and MITRE ATT&CK framework. 
Use the provided context to answer the user's question accurately and comprehensively.

Context from knowledge base:
{context}

Question: {question}

Instructions:
- Answer based primarily on the provided context
- If the context doesn't contain enough information, say so clearly
- For STIX questions, reference specific versions when relevant
- For MITRE ATT&CK questions, mention technique IDs when available
- Be precise and technical when appropriate
- If asked about conversion or validation, mention that specific tools are available

Answer:"""
    
    def _format_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format source information for display"""
        sources = []
        
        for doc in retrieved_docs:
            metadata = doc['metadata']
            sources.append({
                'source': metadata.get('source', 'Unknown'),
                'type': metadata.get('type', 'Unknown'),
                'stix_type': metadata.get('stix_type', ''),
                'relevance': f"{(1 - doc.get('distance', 0)):.2f}"
            })
        
        return sources
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "vector_store_info": self.vector_store.get_collection_info(),
            "model_name": self.model_name,
            "knowledge_base_path": self.knowledge_base_path
        }
    
    def test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': 'Hello'}]
            )
            return True
        except Exception as e:
            self.logger.error(f"Ollama connection test failed: {e}")
            return False