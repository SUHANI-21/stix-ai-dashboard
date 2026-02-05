import json
import pandas as pd
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

class RAGDocumentProcessor:
    """Processes documents from knowledge base"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.logger = logging.getLogger(__name__)
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """Process all documents in knowledge base"""
        documents = []
        
        # Process MITRE ATT&CK data
        mitre_path = os.path.join(self.knowledge_base_path, "mitre_attack")
        if os.path.exists(mitre_path):
            print(f"\n📂 Processing MITRE ATT&CK files...")
            documents.extend(self._process_mitre_data(mitre_path))
            mitre_count = len([d for d in documents if d['metadata'].get('type') != 'stix_schema'])
            print(f"✅ MITRE: {mitre_count} document chunks")
            self.logger.info(f"Processed MITRE data: {mitre_count} documents")
        
        # Process STIX schemas
        schema_path = os.path.join(self.knowledge_base_path, "stix_schemas")
        if os.path.exists(schema_path):
            print(f"\n📄 Processing STIX schema files...")
            documents.extend(self._process_stix_schemas(schema_path))
            schema_count = len([d for d in documents if d['metadata'].get('type') == 'stix_schema'])
            print(f"✅ STIX Schemas: {schema_count} document chunks")
            self.logger.info(f"Processed STIX schemas: {schema_count} documents")
        
        print(f"\n📊 Total document chunks to index: {len(documents)}")
        self.logger.info(f"Total documents processed: {len(documents)}")
        return documents
    
    def _process_mitre_data(self, mitre_path: str) -> List[Dict[str, Any]]:
        """Process JSON and CSV files from MITRE data"""
        documents = []
        files = os.listdir(mitre_path)
        
        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(mitre_path, filename)
            print(f"  [{idx}/{len(files)}] Processing: {filename}...", end=" ", flush=True)
            
            if filename.endswith('.json'):
                docs = self._process_json_file(filepath, filename)
                print(f"✓ ({len(docs)} chunks)")
                documents.extend(docs)
            elif filename.endswith('.csv'):
                docs = self._process_csv_file(filepath, filename)
                print(f"✓ ({len(docs)} chunks)")
                documents.extend(docs)
            else:
                print("⊘ (skipped)")
        
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
            self.logger.warning(f"Error processing {filename}: {e}")
        
        return documents
    
    def _process_csv_file(self, filepath: str, filename: str) -> List[Dict[str, Any]]:
        """Process CSV files"""
        documents = []
        
        try:
            df = pd.read_csv(filepath)
            
            for _, row in df.iterrows():
                content_parts = []
                
                # Build content from all columns
                for col in df.columns:
                    if pd.notna(row[col]):
                        value = str(row[col]).strip()
                        if value:
                            content_parts.append(f"{col}: {value}")
                
                if content_parts:
                    documents.append({
                        "content": "\n".join(content_parts),
                        "metadata": {
                            "source": filename,
                            "type": "csv_row"
                        }
                    })
        
        except Exception as e:
            self.logger.warning(f"Error processing {filename}: {e}")
        
        return documents
    
    def _process_stix_schemas(self, schema_path: str) -> List[Dict[str, Any]]:
        """Process STIX schema HTML files"""
        documents = []
        files = [f for f in os.listdir(schema_path) if f.endswith('.html')]
        
        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(schema_path, filename)
            print(f"  [{idx}/{len(files)}] Processing: {filename}...", end=" ", flush=True)
            docs = self._process_html_file(filepath, filename)
            print(f"✓ ({len(docs)} chunks)")
            documents.extend(docs)
        
        return documents
    
    def _process_html_file(self, filepath: str, filename: str) -> List[Dict[str, Any]]:
        """Process HTML schema files with improved section extraction"""
        documents = []
        
        try:
            # Try multiple encodings for HTML files
            content = None
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                self.logger.warning(f"Could not decode {filename} with any encoding")
                return documents
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract structured sections with headers
            current_section = ""
            current_header = ""
            
            # Find all elements in order
            all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'ol', 'ul'])
            
            for element in all_elements:
                text = element.get_text(strip=True)
                
                # Handle headers
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    # Save previous section if it exists
                    if current_section.strip() and len(current_section) > 100:
                        documents.append({
                            "content": f"{current_header}\n{current_section}".strip(),
                            "metadata": {
                                "source": filename,
                                "type": "stix_schema",
                                "section": current_header.strip()
                            }
                        })
                    
                    # Start new section
                    current_header = text
                    current_section = ""
                
                # Handle content
                elif text and len(text) > 20:
                    current_section += f"\n{text}"
                    
                    # Create document when section gets too large
                    if len(current_section) > 1500:
                        documents.append({
                            "content": f"{current_header}\n{current_section}".strip(),
                            "metadata": {
                                "source": filename,
                                "type": "stix_schema",
                                "section": current_header.strip()
                            }
                        })
                        current_section = ""
            
            # Add final section
            if current_section.strip() and len(current_section) > 100:
                documents.append({
                    "content": f"{current_header}\n{current_section}".strip(),
                    "metadata": {
                        "source": filename,
                        "type": "stix_schema",
                        "section": current_header.strip()
                    }
                })
        
        except Exception as e:
            self.logger.warning(f"Error processing {filepath}: {e}")
        
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
                if len(value) < 500:
                    content_parts.append(f"{key}: {value}")
        
        if not content_parts:
            return None
        
        return {
            "content": "\n".join(content_parts),
            "metadata": {
                "source": source,
                "type": obj_type,
                "id": obj_id
            }
        }
