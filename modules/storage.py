"""
STIX File Storage Module
Handles local file storage for converted STIX data
"""
import json
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime


class STIXStorage:
    """Local file storage for STIX data"""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            # Default to project directory
            self.base_dir = Path(__file__).parent.parent / "data"
        else:
            self.base_dir = Path(base_dir)
        
        # Create directories
        self.converted_dir = self.base_dir / "converted"
        self.original_dir = self.base_dir / "original"
        self.results_dir = self.base_dir / "results"
        
        for dir_path in [self.converted_dir, self.original_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_original_file(self, uploaded_file, file_id):
        """Save original uploaded file"""
        original_path = self.original_dir / f"{file_id}_{uploaded_file.name}"
        with open(original_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return str(original_path)
    
    def save_original_file_bytes(self, file_bytes, filename, file_id):
        """Save original file from bytes"""
        original_path = self.original_dir / f"{file_id}_{filename}"
        with open(original_path, 'wb') as f:
            f.write(file_bytes)
        return str(original_path)
    
    def save_converted_stix(self, stix_data, original_filename, metadata=None):
        """
        Save converted STIX 2.1 data to file
        
        Args:
            stix_data (dict): Converted STIX 2.1 data
            original_filename (str): Original filename
            metadata (dict): Additional metadata
            
        Returns:
            str: File ID for accessing the data
        """
        file_id = str(uuid4())
        
        # Save converted data
        converted_path = self.converted_dir / f"{file_id}.json"
        with open(converted_path, 'w', encoding='utf-8') as f:
            json.dump(stix_data, f, indent=2)
        
        # Save metadata
        meta_data = {
            "file_id": file_id,
            "original_filename": original_filename,
            "converted_path": str(converted_path),
            "original_path": metadata.get("original_path") if metadata else None,
            "created_at": datetime.now().isoformat(),
            "object_count": len(stix_data.get("objects", [])) if isinstance(stix_data, dict) else 0,
            **(metadata or {})
        }
        
        meta_path = self.converted_dir / f"{file_id}_meta.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2)
        
        return file_id
    
    def get_stix_data(self, file_id):
        """Get STIX data by file ID"""
        converted_path = self.converted_dir / f"{file_id}.json"
        if converted_path.exists():
            with open(converted_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_metadata(self, file_id):
        """Get metadata by file ID"""
        meta_path = self.converted_dir / f"{file_id}_meta.json"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_files(self):
        """List all stored files"""
        files = []
        for meta_file in self.converted_dir.glob("*_meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    files.append(metadata)
            except:
                continue
        return sorted(files, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def save_analysis_result(self, file_id, module_name, results):
        """Save analysis results"""
        result_path = self.results_dir / f"{file_id}_{module_name}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    
    def get_analysis_results_list(self, file_id):
        """Get list of all analysis results for a file"""
        results = []
        for result_file in self.results_dir.glob(f"{file_id}_*.json"):
            module_name = result_file.stem.replace(f"{file_id}_", "")
            results.append(module_name)
        return results
    
    def get_analysis_result(self, file_id, module_name):
        """Get analysis results"""
        result_path = self.results_dir / f"{file_id}_{module_name}.json"
        if result_path.exists():
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None