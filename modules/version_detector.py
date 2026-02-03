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
    except:
        pass

    # Try XML (STIX 1.x)
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        if "STIX_Package" in root.tag:
            return "STIX 1.x"
    except:
        pass

    return "Unknown STIX Format"
