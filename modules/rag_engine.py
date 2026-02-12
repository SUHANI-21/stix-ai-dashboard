import ollama
from typing import List, Dict, Any, Optional
import logging
from .vector_store import VectorStoreManager
from .rag_processor import RAGDocumentProcessor
from .mitre_lookup import MITRELookup
from .web_search import WebSearchEnricher

class RAGEngine:
    def __init__(self, knowledge_base_path: str = "knowledge_base", model_name: str = "llama3.2:3b"):
        self.knowledge_base_path = knowledge_base_path
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.processor = RAGDocumentProcessor(knowledge_base_path)
        self.vector_store = VectorStoreManager()
        self.mitre_lookup = MITRELookup(knowledge_base_path)
        self.web_search = WebSearchEnricher()
        
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
    
    def query(self, question: str, n_results: int = 8) -> Dict[str, Any]:
        """Process a query using RAG"""
        try:
            # Check for direct tool questions - bypass RAG entirely
            question_lower = question.lower()
            
            # STIX conversion questions
            if any(word in question_lower for word in ['convert', 'conversion', 'stix 1', 'stix 2']):
                if 'stix 1' in question_lower or '1.x' in question_lower:
                    return {
                        "answer": """To convert STIX 1.x to STIX 2.1:

**Use the Version Detector & Validator tool in this dashboard:**
1. Navigate to "Version Detector & Validator" in the sidebar
2. Upload your STIX 1.x XML file
3. The tool will automatically detect the version and convert it to STIX 2.1 JSON format
4. Download the converted file

Note: STIX 1.x uses XML format, while STIX 2.0/2.1 uses JSON format. The conversion handles all structural and format changes automatically.""",
                        "sources": [{"source": "Dashboard Tool", "type": "tool", "relevance": "1.00"}],
                        "retrieved_docs": 0
                    }
            
            # Validation questions
            if any(word in question_lower for word in ['validate', 'validation', 'check']):
                if 'stix' in question_lower:
                    return {
                        "answer": """To validate STIX files:

**Use the Version Detector & Validator tool:**
1. Navigate to "Version Detector & Validator" in the sidebar
2. Upload your STIX JSON file
3. The tool will validate it against the official STIX 2.0/2.1 specifications
4. View validation results and any errors or warnings""",
                        "sources": [{"source": "Dashboard Tool", "type": "tool", "relevance": "1.00"}],
                        "retrieved_docs": 0
                    }
            
            # Mapping questions
            if any(word in question_lower for word in ['map', 'mapping', 'mitre', 'att&ck', 'attack']):
                if not any(word in question_lower for word in ['t1', 'technique', 'explain', 'what is']):
                    return {
                        "answer": """To map indicators to MITRE ATT&CK techniques:

**Use the Attack Mapping tool:**
1. Navigate to "Attack Mapping" in the sidebar
2. Upload your STIX file or enter indicators
3. The tool will automatically map them to relevant MITRE ATT&CK techniques
4. View the mapped techniques with tactics and descriptions""",
                        "sources": [{"source": "Dashboard Tool", "type": "tool", "relevance": "1.00"}],
                        "retrieved_docs": 0
                    }
            
            # Check if this is a MITRE technique query - use web search directly
            tech_id = self.web_search.is_mitre_technique(question)
            if tech_id:
                web_info = self.web_search.enrich_with_web_search(question)
                if web_info:
                    response = self._generate_response_from_web(question, web_info)
                    return {
                        "answer": response,
                        "sources": [{"source": "attack.mitre.org", "type": "web", "relevance": "1.00"}],
                        "retrieved_docs": 1
                    }
            
            # Retrieve relevant documents
            self.logger.info(f"Searching for relevant documents for: {question}")
            retrieved_docs = self.vector_store.search(question, n_results)
            
            # Filter out low-quality results
            retrieved_docs = [doc for doc in retrieved_docs 
                            if doc['metadata'].get('stix_type') not in ['marking-definition', 'identity']
                            and doc.get('distance', 1.0) < 0.7]
            
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
    
    def _generate_response_from_web(self, question: str, web_info: str) -> str:
        """Generate response using web-scraped information"""
        prompt = f"""You are a cybersecurity expert specializing in MITRE ATT&CK framework.

Official information from attack.mitre.org:
{web_info}

Question: {question}

Instructions:
- Provide a clear, accurate answer based on the official MITRE ATT&CK information above
- Include: Technique ID, Name, Tactics, Description, and Platforms
- Be concise but comprehensive
- Do NOT confuse STIX (the data format) with MITRE ATT&CK (the knowledge base)
- STIX is used to represent threat intelligence data, MITRE ATT&CK is a knowledge base of adversary tactics and techniques
- If relevant, mention that this dashboard has tools for STIX conversion, validation, and MITRE mapping in the sidebar

Answer:"""
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return f"Error generating response: {str(e)}"
    
    def _generate_response(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate response using Ollama"""
        # Build context from retrieved documents
        context = self._build_context(retrieved_docs)
        
        # Enrich with MITRE lookup if technique ID detected
        context = self._enrich_context_with_mitre(question, context)
        
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
            stix_version = doc['metadata'].get('stix_version', '')
            content = doc['content'][:2000]  # Increased from 1000 to 2000 for more context
            
            # Add version info if available
            version_info = f" [Version: {stix_version}]" if stix_version else ""
            context_parts.append(f"Document {i} (Source: {source}, Type: {doc_type}{version_info}):\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _enrich_context_with_mitre(self, question: str, context: str) -> str:
        """Enrich context with MITRE technique lookup if applicable"""
        # Try local lookup first
        enriched = self.mitre_lookup.enrich_context(question, context)
        
        # If local lookup didn't add anything, try web search
        if enriched == context:
            web_info = self.web_search.enrich_with_web_search(question)
            if web_info:
                enriched = web_info + "\n" + context
        
        return enriched
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for the LLM"""
        return f"""You are a cybersecurity threat intelligence expert assistant.

=== KNOWLEDGE DOMAINS ===

1. STIX (Structured Threat Information Expression)
   - A JSON-based language for representing cyber threat intelligence
   - Defines objects like Indicator, Malware, Threat-Actor, Attack-Pattern, etc.
   - Current versions: 2.0 and 2.1 (JSON format)
   - Legacy: 1.x (XML format)
   - When asked about STIX: Focus on object properties, relationships, and data structure

2. TAXII (Trusted Automated Exchange of Intelligence Information)
   - A protocol for exchanging STIX data over HTTPS
   - Defines APIs for sharing threat intelligence
   - When asked about TAXII: Focus on endpoints, collections, and transport mechanisms

3. MITRE ATT&CK
   - A knowledge base of adversary tactics and techniques (NOT a data format)
   - Techniques identified by IDs like T1566, T1059.001
   - Can be represented using STIX format
   - When asked about ATT&CK: Focus on adversary behavior, tactics, and detection

4. MITRE ATLAS  
   - Knowledge base for adversarial ML threats
   - Techniques identified by IDs like AML.T0001
   - When asked about ATLAS: Focus on AI/ML attack techniques

=== QUESTION TYPE HANDLERS ===

IF question is about a STIX object (Indicator, Malware, etc.):
- Provide a properties table with: Property | Type | Required | Description
- Include common properties (type, id, created, modified, etc.)
- Add object-specific properties
- Show a JSON example
- Mention relationships to other objects

IF question is about a MITRE technique (T#### or AML.T####):
- Use the official information provided in context
- Format: ID, Name, Tactics, Platforms, Description
- Include detection methods if available

IF question is about conversion/validation/mapping:
- Refer to the specific dashboard tool
- Give brief context, then direct to tool

IF question is conceptual:
- Synthesize from all provided context
- Be clear and concise
- Use examples when helpful

=== AVAILABLE DASHBOARD TOOLS ===
1. Version Detector & Validator - Detect/validate STIX files
2. SDO Similarity Search - Find similar STIX objects
3. Attack Mapping - Map to MITRE ATT&CK
4. Malware Classifier - Classify malware
5. Credibility Assessment - Assess source credibility
6. File Browser - Manage STIX files

=== CONTEXT ===
{context}

=== QUESTION ===
{question}

=== YOUR RESPONSE ===
Provide a clear, accurate, well-formatted answer:"""
    
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