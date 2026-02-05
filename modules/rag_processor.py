import json
import pandas as pd
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

class RAGDocumentProcessor:
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.logger = logging.getLogger(__name__)
        
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """Process all documents in knowledge base and return chunks"""
        documents = []
        
        # Process MITRE ATT&CK data
        mitre_path = os.path.join(self.knowledge_base_path, "mitre_attack")
        if os.path.exists(mitre_path):
            documents.extend(self._process_mitre_data(mitre_path))
            
        # Process STIX schemas
        schema_path = os.path.join(self.knowledge_base_path, "stix_schemas")
        if os.path.exists(schema_path):
            documents.extend(self._process_stix_schemas(schema_path))
            
        self.logger.info(f"Processed {len(documents)} document chunks")
        return documents
    
    def _process_mitre_data(self, mitre_path: str) -> List[Dict[str, Any]]:
        """Process JSON and CSV files from MITRE data"""
        documents = []
        
        for filename in os.listdir(mitre_path):
            filepath = os.path.join(mitre_path, filename)
            
            if filename.endswith('.json'):
                documents.extend(self._process_json_file(filepath, filename))
            elif filename.endswith('.csv'):
                documents.extend(self._process_csv_file(filepath, filename))
                
        return documents
    
    def _process_json_file(self, filepath: str, filename: str) -> List[Dict[str, Any]]:
        """Process MITRE JSON files"""
        documents = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle STIX bundle format
            if isinstance(data, dict) and 'objects' in data:
                objects = data['objects']
            elif isinstance(data, list):
                objects = data
            else:
                objects = [data]
            
            for obj in objects:
                if isinstance(obj, dict):
                    doc = self._create_document_from_object(obj, filename)
                    if doc:
                        documents.append(doc)
                        
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {e}")
            
        return documents
    
    def _process_csv_file(self, filepath: str, filename: str) -> List[Dict[str, Any]]:
        """Process CSV files with summaries"""
        documents = []
        
        try:
            df = pd.read_csv(filepath)
            
            for _, row in df.iterrows():
                content = ""
                metadata = {"source": filename, "type": "csv"}
                
                # Build content from all columns
                for col in df.columns:
                    if pd.notna(row[col]):
                        content += f"{col}: {row[col]}\n"
                        
                if content.strip():
                    documents.append({
                        "content": content.strip(),
                        "metadata": metadata
                    })
                    
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {e}")
            
        return documents
    
    def _process_stix_schemas(self, schema_path: str) -> List[Dict[str, Any]]:
        """Process STIX schema HTML files"""
        documents = []
        
        for filename in os.listdir(schema_path):
            if filename.endswith('.html'):
                filepath = os.path.join(schema_path, filename)
                documents.extend(self._process_html_file(filepath, filename))
                
        return documents
    
    def _process_html_file(self, filepath: str, filename: str) -> List[Dict[str, Any]]:
        """Process HTML schema files"""
        documents = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract text from sections
            sections = soup.find_all(['h1', 'h2', 'h3', 'h4', 'section', 'div'])
            
            for section in sections:
                text = section.get_text(strip=True)
                if len(text) > 100:  # Only meaningful sections
                    documents.append({
                        "content": text[:2000],  # Limit chunk size
                        "metadata": {
                            "source": filename,
                            "type": "stix_schema"
                        }
                    })
                    
        except Exception as e:
            self.logger.error(f"Error processing {filepath}: {e}")
            
        return documents
    
    def _create_document_from_object(self, obj: Dict, source: str) -> Dict[str, Any]:
        """Create document from STIX object"""
        content_parts = []
        
        # Extract key fields
        obj_type = obj.get('type', 'unknown')
        obj_id = obj.get('id', '')
        name = obj.get('name', '')
        description = obj.get('description', '')
        
        if name:
            content_parts.append(f"Name: {name}")
        if description:
            content_parts.append(f"Description: {description}")
            
        # Add other relevant fields
        for key, value in obj.items():
            if key not in ['type', 'id', 'name', 'description'] and isinstance(value, str):
                if len(value) < 500:  # Avoid very long fields
                    content_parts.append(f"{key}: {value}")
        
        if not content_parts:
            return None
            
        return {
            "content": "\n".join(content_parts),
            "metadata": {
                "source": source,
                "type": obj_type,
                "id": obj_id,
                "stix_type": obj_type
            }
        }