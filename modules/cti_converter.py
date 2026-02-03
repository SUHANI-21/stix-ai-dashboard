import json

def convert_to_common_cti(file_path):
    with open(file_path) as f:
        data = json.load(f)

    common_cti = []

    for obj in data.get("objects", []):
        entry = {
            "type": obj.get("type"),
            "name": obj.get("name"),
            "description": obj.get("description"),
            "confidence": obj.get("confidence", 50)
        }
        common_cti.append(entry)

    return common_cti
