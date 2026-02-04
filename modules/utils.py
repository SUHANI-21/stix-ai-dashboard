"""
Utility Functions - File handling, cleanup, and session management
"""
import tempfile
import os
import shutil
from pathlib import Path
import json


class FileManager:
    """Manage temporary file uploads and cleanup"""
    
    # Session-based temp directory
    TEMP_DIR = None
    
    @classmethod
    def initialize_session_temp(cls):
        """Initialize a temp directory for this session"""
        if cls.TEMP_DIR is None:
            cls.TEMP_DIR = tempfile.mkdtemp(prefix="stix_analyzer_")
        return cls.TEMP_DIR
    
    @classmethod
    def get_temp_dir(cls):
        """Get the session temp directory"""
        if cls.TEMP_DIR is None:
            cls.initialize_session_temp()
        return cls.TEMP_DIR
    
    @classmethod
    def save_uploaded_file(cls, uploaded_file):
        """
        Save uploaded file to session temp directory
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            str: Path to saved file
        """
        temp_dir = cls.get_temp_dir()
        file_path = Path(temp_dir) / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(file_path)
    
    @classmethod
    def cleanup_session(cls):
        """Delete all files in session temp directory"""
        if cls.TEMP_DIR and os.path.exists(cls.TEMP_DIR):
            try:
                shutil.rmtree(cls.TEMP_DIR)
                cls.TEMP_DIR = None
            except Exception as e:
                print(f"Error cleaning up temp files: {str(e)}")
    
    @classmethod
    def list_temp_files(cls):
        """List all files in temp directory"""
        temp_dir = cls.get_temp_dir()
        try:
            return os.listdir(temp_dir)
        except:
            return []


class JsonHelper:
    """Helper functions for JSON processing"""
    
    @staticmethod
    def safe_json_parse(content):
        """Safely parse JSON content"""
        try:
            return json.loads(content), None
        except json.JSONDecodeError as e:
            return None, f"JSON Parse Error: {str(e)}"
    
    @staticmethod
    def pretty_print_json(data, indent=2):
        """Pretty print JSON data"""
        try:
            return json.dumps(data, indent=indent)
        except Exception as e:
            return f"Error formatting JSON: {str(e)}"
    
    @staticmethod
    def extract_objects_from_bundle(data):
        """Extract objects from a STIX bundle"""
        if isinstance(data, dict) and data.get("type") == "bundle":
            return data.get("objects", [])
        return []


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def format_error_message(error_type, error_msg):
        """Format error message for user display"""
        error_messages = {
            "file_read": f"❌ Failed to read file: {error_msg}",
            "file_parse": f"❌ Failed to parse file: {error_msg}",
            "file_format": f"❌ Unsupported file format: {error_msg}",
            "validation": f"❌ Validation failed: {error_msg}",
            "conversion": f"❌ Conversion failed: {error_msg}",
            "unknown": f"❌ Unknown error: {error_msg}"
        }
        return error_messages.get(error_type, error_messages["unknown"])
    
    @staticmethod
    def create_error_object(error_type, message, details=None):
        """Create structured error object"""
        return {
            "type": error_type,
            "message": message,
            "details": details,
            "friendly_message": ErrorHandler.format_error_message(error_type, message)
        }


class ConversionHelper:
    """Helper functions for STIX conversion"""
    
    @staticmethod
    def get_conversion_output_path(version, base_dir=None):
        """Get the output path for converted STIX file"""
        if base_dir is None:
            base_dir = FileManager.get_temp_dir()
        
        if version and "1." in str(version):
            output_dir = Path(base_dir) / "converted_from_1x"
        else:
            output_dir = Path(base_dir) / "converted_from_2x"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir)
