try:
    import ollama
except ImportError:
    ollama = None

from typing import List, Dict, Any
import logging
from .vector_store import VectorStoreManager
from .rag_processor import RAGDocumentProcessor


class RAGEngine:
    """RAG Engine for STIX Intelligence Q&A"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base", model_name: str = "gpt-oss:20b"):
        self.knowledge_base_path = knowledge_base_path
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.processor = RAGDocumentProcessor(knowledge_base_path)
        self.vector_store = VectorStoreManager()
        
        # Check if index exists
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
            self.logger.info("✅ Index built successfully")
        else:
            self.logger.warning("⚠️ No documents found to index")
    
    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Process a query using RAG"""
        try:
            # Retrieve relevant documents
            self.logger.info(f"Searching for documents: {question}")
            retrieved_docs = self.vector_store.search(question, n_results)
            
            if not retrieved_docs:
                return {
                    "answer": "No relevant information found in knowledge base.",
                    "sources": [],
                    "retrieved_docs": 0
                }
            
            # Generate response
            response = self._generate_response(question, retrieved_docs)
            
            return {
                "answer": response,
                "sources": self._format_sources(retrieved_docs),
                "retrieved_docs": len(retrieved_docs)
            }
        
        except Exception as e:
            self.logger.error(f"Query error: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "sources": [],
                "retrieved_docs": 0
            }
    
    def _generate_response(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate response using Ollama"""
        if ollama is None:
            return "Ollama not installed. Install with: pip install ollama"
        
        context = self._build_context(retrieved_docs)
        prompt = self._create_prompt(question, context)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )
            return response['message']['content']
        
        except Exception as e:
            self.logger.error(f"Ollama error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Build enhanced context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc['metadata'].get('source', 'Unknown')
            doc_type = doc['metadata'].get('type', 'Unknown')
            section = doc['metadata'].get('section', '')
            content = doc['content'][:1200]  # Increased for better context
            
            header = f"[{i}] {source}"
            if section:
                header += f" - {section}"
            header += f" ({doc_type}):"
            
            context_parts.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create enhanced prompt for better STIX intelligence responses"""
        return f"""You are an expert cybersecurity analyst specializing in STIX (Structured Threat Information eXpression), MITRE ATT&CK framework, and threat intelligence analysis.

Your expertise includes:
- STIX 2.0/2.1 object models, relationships, and patterning
- MITRE ATT&CK tactics, techniques, and procedures (TTPs)
- Threat actor profiling and campaign analysis
- Malware analysis and attribution
- Cyber observable analysis and IOC validation
- Threat intelligence credibility assessment

CONTEXT INFORMATION:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Provide detailed, technical responses based on the context
- Reference sources using [1], [2], etc. when citing information
- For STIX queries: Include object structure, properties, and relationships
- For threat intelligence: Provide attribution, confidence levels, and analysis
- For technical questions: Give practical examples and implementation guidance
- If analyzing threats: Assess credibility, provide confidence scores, and suggest validation steps
- If context is insufficient, clearly state limitations and suggest additional research
- Use proper cybersecurity terminology and be precise

RESPONSE:"""
    
    def _format_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format sources for display"""
        sources = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc['metadata']
            relevance = max(0, 1 - doc.get('distance', 0))
            
            sources.append({
                'id': str(i),
                'source': metadata.get('source', 'Unknown'),
                'type': metadata.get('type', 'Unknown'),
                'relevance': f"{relevance:.0%}"
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
        """Test Ollama connection"""
        if ollama is None:
            return False
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': 'test'}],
                stream=False
            )
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
