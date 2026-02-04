"""
UUID Validator and Fixer Module
Validates and fixes invalid UUIDs in STIX objects
"""
import re
import json
from uuid import uuid4
from typing import Dict, List, Tuple


class UUIDFixer:
    """Validate and fix UUIDs in STIX objects"""
    
    # Valid UUID v4 pattern (DCE 1.1, ISO/IEC 11578:1996)
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    # STIX object types that have IDs
    STIX_TYPES_WITH_IDS = {
        'indicator', 'malware', 'campaign', 'identity', 'threat-actor',
        'attack-pattern', 'tool', 'vulnerability', 'relationship',
        'sighting', 'observed-data', 'opinion', 'report', 'bundle',
        'x-custom', 'extension', 'marking-definition'
    }

    @classmethod
    def is_valid_uuid(cls, uuid_str: str) -> bool:
        """Check if UUID is valid"""
        if not isinstance(uuid_str, str):
            return False
        return cls.UUID_PATTERN.match(uuid_str) is not None

    @classmethod
    def fix_uuid(cls, invalid_uuid: str) -> str:
        """
        Fix an invalid UUID by generating a valid one
        
        Args:
            invalid_uuid (str): Invalid UUID or ID string
            
        Returns:
            str: Valid UUID v4
        """
        # If somehow it's already valid, return it
        if cls.is_valid_uuid(invalid_uuid):
            return invalid_uuid
        
        # Generate a new valid UUID v4
        return str(uuid4())

    @classmethod
    def validate_and_fix_bundle(cls, bundle_data: Dict) -> Tuple[Dict, List[str]]:
        """
        Validate and fix all UUIDs in a STIX bundle
        
        Args:
            bundle_data (dict): STIX bundle
            
        Returns:
            tuple: (fixed_bundle, list_of_changes_made)
        """
        changes = []
        bundle_copy = json.loads(json.dumps(bundle_data))  # Deep copy
        
        # Fix bundle ID if present
        if "id" in bundle_copy:
            if not cls.is_valid_uuid(bundle_copy["id"]):
                old_id = bundle_copy["id"]
                bundle_copy["id"] = f"bundle--{uuid4()}"
                changes.append(f"Fixed Bundle ID: {old_id} → {bundle_copy['id']}")
        
        # Fix object IDs and create mapping
        id_mapping = {}  # Map old IDs to new IDs
        
        if "objects" in bundle_copy:
            objects = bundle_copy["objects"]
            
            for obj in objects:
                if isinstance(obj, dict) and "id" in obj:
                    obj_id = obj["id"]
                    
                    # Check if it's a valid STIX ID format (type--uuid)
                    if "--" in obj_id:
                        parts = obj_id.split("--", 1)
                        if len(parts) == 2:
                            obj_type, uuid_part = parts
                            
                            if not cls.is_valid_uuid(uuid_part):
                                old_id = obj_id
                                new_uuid = str(uuid4())
                                new_id = f"{obj_type}--{new_uuid}"
                                
                                id_mapping[old_id] = new_id
                                obj["id"] = new_id
                                changes.append(f"Fixed {obj_type} ID: {old_id} → {new_id}")
                    else:
                        # No type prefix - invalid format
                        old_id = obj_id
                        new_id = f"unknown--{uuid4()}"
                        id_mapping[old_id] = new_id
                        obj["id"] = new_id
                        changes.append(f"Fixed invalid ID format: {old_id} → {new_id}")
            
            # Fix references to old IDs in relationships
            for obj in objects:
                if isinstance(obj, dict):
                    # Fix created_by_ref
                    if "created_by_ref" in obj and obj["created_by_ref"] in id_mapping:
                        obj["created_by_ref"] = id_mapping[obj["created_by_ref"]]
                    
                    # Fix object_ref in relationships
                    if obj.get("type") == "relationship":
                        if "source_ref" in obj and obj["source_ref"] in id_mapping:
                            obj["source_ref"] = id_mapping[obj["source_ref"]]
                        if "target_ref" in obj and obj["target_ref"] in id_mapping:
                            obj["target_ref"] = id_mapping[obj["target_ref"]]
                    
                    # Fix object_refs in observed-data and reports
                    if "object_refs" in obj and isinstance(obj["object_refs"], list):
                        obj["object_refs"] = [
                            id_mapping.get(ref, ref) for ref in obj["object_refs"]
                        ]
                    
                    # Fix sighting_of_ref
                    if "sighting_of_ref" in obj and obj["sighting_of_ref"] in id_mapping:
                        obj["sighting_of_ref"] = id_mapping[obj["sighting_of_ref"]]
                    
                    # Fix observed_object_refs
                    if "observed_object_refs" in obj and isinstance(obj["observed_object_refs"], list):
                        obj["observed_object_refs"] = [
                            id_mapping.get(ref, ref) for ref in obj["observed_object_refs"]
                        ]
        
        return bundle_copy, changes

    @classmethod
    def get_fix_report(cls, bundle_data: Dict) -> Dict:
        """
        Get a detailed report of all invalid UUIDs found
        
        Args:
            bundle_data (dict): STIX bundle
            
        Returns:
            dict: Report with findings
        """
        report = {
            "invalid_uuids_found": [],
            "invalid_count": 0,
            "objects_checked": 0
        }
        
        if "objects" in bundle_data:
            for obj in bundle_data["objects"]:
                if isinstance(obj, dict):
                    report["objects_checked"] += 1
                    obj_id = obj.get("id", "")
                    
                    if obj_id and not cls.is_valid_uuid(obj_id.split("--")[-1] if "--" in obj_id else obj_id):
                        report["invalid_uuids_found"].append({
                            "object_type": obj.get("type", "unknown"),
                            "invalid_id": obj_id
                        })
                        report["invalid_count"] += 1
        
        return report
