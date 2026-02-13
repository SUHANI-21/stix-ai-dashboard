import os
import json
import csv
from collections import defaultdict
from pathlib import Path


SDOs=["attack-pattern",
      "campaign",
      "course-of-action", 
      "identity",
      "incident",
      "indicator",
      "infrastructure",
      "intrusion-set",
      "location",
      "malware",
      "malware-analysis",
      "note",
      "threat-actor",
      "tool",
      "vulnerability",
      ] 

def normalize_value(value):
    """
    Convert lists/dicts into JSON strings so CSVs remain valid.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value

def stix_json_to_csv(json_file: str):
    """
    Docstring for stix_json_to_csv
    
    :param json_file: Description
    :type json_file: str
    :param csv_file: Description
    :type csv_file: str
    """
    with open(json_file, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    

    csv_file=Path(json_file).stem+".csv"
    csv_path=Path("modules/json_2_csv_files")/csv_file
    csv_path.parent.mkdir(parents=True, exist_ok=True)


    if bundle.get("type") != "bundle":
        raise ValueError("Input JSON is not a STIX bundle")

    # Filter only required SDOs
    objects = [
        obj for obj in bundle.get("objects", [])
        if obj.get("type") in SDOs
    ]

    if not objects:
        print("[!] No matching SDO objects found in bundle")
        return

    # Collect all fields
    all_fields = set()
    for obj in objects:
        all_fields.update(obj.keys())

    all_fields = sorted(all_fields)

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()

        for obj in objects:
            row = {field: normalize_value(obj.get(field)) for field in all_fields}
            writer.writerow(row)

    print(f"[+] Written {csv_file} ({len(objects)} rows)")
    return csv_path



