import json
import xml.etree.ElementTree as ET

def detect_stix_version(file_path):
    # Try JSON first (STIX 2.x)
    try:
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        if "spec_version" in data:
            return f"STIX {data['spec_version']}"
        elif data.get("type") == "bundle":
            return "STIX 2.0 (likely)"
        # Check if it's a single STIX object
        elif data.get("type") and data.get("id"):
            return "STIX 2.1"  # Assume 2.1 for individual objects
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    # Try XML (STIX 1.x)
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check namespace for version
        if "stix.mitre.org/stix-1" in str(root.tag):
            return "STIX 1.x"
        elif "stix" in root.tag.lower():
            return "STIX 1.x (likely)"
    except ET.ParseError:
        pass
    
    return "Unknown format"
