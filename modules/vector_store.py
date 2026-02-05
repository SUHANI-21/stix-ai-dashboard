import chromadb
import os
import time
import uuid
from typing import List, Dict, Any
import logging

class VectorStoreManager:
    """Manages ChromaDB vector store for RAG"""
    
    def __init__(self, persist_directory: str = "knowledge_base/embeddings"):
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB with default embedding function
        os.makedirs(persist_directory, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
        except Exception as e:
            self.logger.error(f"Error initializing ChromaDB: {e}")
            raise
        
        # Get or create collection (ChromaDB handles embeddings internally)
        try:
            self.collection = self.client.get_or_create_collection(
                name="stix_knowledge_base",
                metadata={"description": "STIX and MITRE ATT&CK knowledge base"}
            )
            self.logger.info("Vector store initialized successfully")
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector store"""
        if not documents:
            self.logger.warning("No documents to add")
            return False
        # Use batching to avoid ChromaDB maximum-batch-size errors.
        BATCH_SIZE = 2048
        total = len(documents)
        batch_count = (total + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n🔄 Indexing {total} documents in ChromaDB in {batch_count} batches...")
        added = 0

        for batch_idx, start in enumerate(range(0, total, BATCH_SIZE), start=1):
            batch = documents[start:start + BATCH_SIZE]
            ids = [f"doc_{start + i}_{uuid.uuid4().hex[:8]}" for i in range(len(batch))]
            contents = [d['content'] for d in batch]
            metadatas = [d.get('metadata', {}) for d in batch]

            # Retry logic for transient ChromaDB errors
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    self.collection.add(
                        ids=ids,
                        documents=contents,
                        metadatas=metadatas
                    )
                    added += len(batch)
                    print(f"  Indexed: {added}/{total} documents (Batch {batch_idx}/{batch_count})", flush=True)
                    break
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt} failed adding batch {batch_idx}: {e}")
                    if attempt < max_retries:
                        time.sleep(1 * attempt)
                        continue
                    else:
                        self.logger.error(f"Failed to add batch {batch_idx} after {max_retries} attempts: {e}")
                        return False

        print(f"✅ Successfully added {added} documents to vector store\n")
        self.logger.info(f"Added {added} documents to vector store")
        return True
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {"document_count": 0, "collection_name": "stix_knowledge_base"}
    
    def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        try:
            self.client.delete_collection(name="stix_knowledge_base")
            self.collection = self.client.get_or_create_collection(
                name="stix_knowledge_base",
                metadata={"description": "STIX and MITRE ATT&CK knowledge base"}
            )
            self.logger.info("Cleared vector store collection")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing collection: {e}")
            return False
    
    def rebuild_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Rebuild the entire index"""
        if not self.clear_collection():
            return False
        return self.add_documents(documents)
