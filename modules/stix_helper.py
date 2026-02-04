"""
STIX Helper Module for Team Integration
Simple functions for teammates to access stored STIX data
"""
import json
from pathlib import Path
from .storage import STIXStorage


# Initialize storage (teammates just import this)
storage = STIXStorage()


def get_stix_data(file_id):
    """
    Get STIX data by file ID - teammates use this function
    
    Args:
        file_id (str): File ID from conversion process
        
    Returns:
        dict: STIX 2.1 data or None if not found
    """
    return storage.get_stix_data(file_id)


def get_file_info(file_id):
    """
    Get file metadata by file ID
    
    Args:
        file_id (str): File ID from conversion process
        
    Returns:
        dict: File metadata or None if not found
    """
    return storage.get_metadata(file_id)


def save_analysis_results(file_id, module_name, results):
    """
    Save analysis results - teammates use this to store their results
    
    Args:
        file_id (str): File ID from conversion process
        module_name (str): Name of analysis module (e.g., "threat_analyzer")
        results (dict): Analysis results to save
    """
    storage.save_analysis_result(file_id, module_name, results)


def get_analysis_results(file_id, module_name):
    """
    Get analysis results from another module
    
    Args:
        file_id (str): File ID from conversion process
        module_name (str): Name of analysis module
        
    Returns:
        dict: Analysis results or None if not found
    """
    return storage.get_analysis_result(file_id, module_name)


def list_all_files():
    """
    List all stored STIX files
    
    Returns:
        list: List of file metadata dictionaries
    """
    return storage.list_files()


# Example usage for teammates:
"""
# Import the helper
from modules.stix_helper import get_stix_data, save_analysis_results

# Get STIX data for analysis
def analyze_threats(file_id):
    stix_data = get_stix_data(file_id)
    if not stix_data:
        return {"error": "File not found"}
    
    # Your analysis code here
    threats = []
    for obj in stix_data.get("objects", []):
        if obj.get("type") == "indicator":
            threats.append(obj)
    
    results = {"threat_count": len(threats), "threats": threats}
    
    # Save results
    save_analysis_results(file_id, "threat_analyzer", results)
    
    return results
"""