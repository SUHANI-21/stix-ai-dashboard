import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

class VectorStoreManager:
    def __init__(self, persist_directory: str = "knowledge_base/embeddings"):
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # Load or create index
        self.index_path = os.path.join(persist_directory, "faiss.index")
        self.metadata_path = os.path.join(persist_directory, "metadata.pkl")
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.documents = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to vector store"""
        if not documents:
            self.logger.warning("No documents to add")
            return
        
        texts = [doc['content'] for doc in documents]
        
        self.logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        self.index.add(np.array(embeddings).astype('float32'))
        self.documents.extend(documents)
        
        self._save()
        self.logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if len(self.documents) == 0:
            return []
        
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), n_results)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    'content': self.documents[idx]['content'],
                    'metadata': self.documents[idx]['metadata'],
                    'distance': float(distances[0][i])
                })
        
        return results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        return {
            "document_count": len(self.documents),
            "collection_name": "stix_knowledge_base"
        }
    
    def clear_collection(self):
        """Clear all documents from collection"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._save()
        self.logger.info("Cleared vector store collection")
    
    def rebuild_index(self, documents: List[Dict[str, Any]]):
        """Rebuild the entire index"""
        self.clear_collection()
        self.add_documents(documents)
    
    def _save(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.documents, f)