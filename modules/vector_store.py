import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict, Any
import logging

class VectorStoreManager:
    def __init__(self, persist_directory: str = "knowledge_base/embeddings"):
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="stix_knowledge_base",
            metadata={"description": "STIX and MITRE ATT&CK knowledge base"}
        )
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to vector store"""
        if not documents:
            self.logger.warning("No documents to add")
            return
            
        # Prepare data for ChromaDB
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            texts.append(doc['content'])
            metadatas.append(doc['metadata'])
            ids.append(f"doc_{i}")
            
        # Generate embeddings
        self.logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        self.logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else 0
            })
            
        return formatted_results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        count = self.collection.count()
        return {
            "document_count": count,
            "collection_name": self.collection.name
        }
    
    def clear_collection(self):
        """Clear all documents from collection"""
        self.client.delete_collection(name="stix_knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="stix_knowledge_base",
            metadata={"description": "STIX and MITRE ATT&CK knowledge base"}
        )
        self.logger.info("Cleared vector store collection")
    
    def rebuild_index(self, documents: List[Dict[str, Any]]):
        """Rebuild the entire index"""
        self.clear_collection()
        self.add_documents(documents)