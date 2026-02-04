import json
import xml.etree.ElementTree as ET

def detect_stix_version(file_path):
    # Try JSON first (STIX 2.x)
    try:
        with open(file_path) as f:
            data = json.load(f)

        if "spec_version" in data:
            return f"STIX {data['spec_version']}"
        elif data.get("type") == "bundle":
            return "STIX 2.0 (likely)"
        # Check if it's a single STIX object
        elif data.get("type") and data.get("id"):
            return "STIX 2.1"  # Assume 2.1 for individual objects
