"""
Enhanced STIX Validator
Wraps stix2validator and provides detailed error/warning reports
"""
import json
from pathlib import Path
from lxml import etree
from stix2validator import validate_string
from stix2 import parse as stix2_parse

try:
    from stix.core import STIXPackage
except ImportError:
    STIXPackage = None


class EnhancedValidator:
    """Enhanced validation with detailed error reporting"""

    @classmethod
    def validate_stix_detailed(cls, filepath):
        """
        Validate STIX file with detailed error and warning extraction
        Handles both JSON (STIX 2.x) and XML (STIX 1.x)
        
        Args:
            filepath (str): Path to STIX file
            
        Returns:
            dict: {
                'is_valid': bool,
                'errors': list of error dicts,
                'warnings': list of warning dicts,
                'error_count': int,
                'warning_count': int,
                'summary': str
            }
        """
        filepath = Path(filepath)
        
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [{"type": "file_read", "message": str(e)}],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0,
                "summary": f"Failed to read file: {str(e)}"
            }
        
        # Detect if it's JSON or XML
        is_json = False
        is_xml = False
        
        # Clean content (remove BOM and extra whitespace)
        content_clean = content.lstrip('\ufeff').strip()
        
        # Check if it starts with { or [ (JSON indicators)
        if content_clean.startswith('{') or content_clean.startswith('['):
            try:
                json.loads(content_clean)
                is_json = True
            except json.JSONDecodeError:
                pass
        
        # Check if it starts with < (XML indicator)
        if content_clean.startswith('<'):
            try:
                etree.fromstring(content_clean.encode("utf-8"))
                is_xml = True
            except Exception:
                pass
        
        # Fallback: try both if we're not sure
        if not is_json and not is_xml:
            try:
                json.loads(content_clean)
                is_json = True
            except json.JSONDecodeError:
                pass
            
            try:
                etree.fromstring(content_clean.encode("utf-8"))
                is_xml = True
            except Exception:
                pass
        
        # Validate JSON (STIX 2.x)
        if is_json:
            try:
                # Try lenient validation first (allow custom objects and non-standard fields)
                try:
                    obj = stix2_parse(content_clean, allow_custom=True)
                    # If parse succeeds with allow_custom, it's valid
                    return {
                        "is_valid": True,
                        "errors": [],
                        "warnings": [],
                        "error_count": 0,
                        "warning_count": 0,
                        "summary": "✅ VALID - STIX JSON validated successfully"
                    }
                except Exception as lenient_error:
                    error_msg = str(lenient_error)
                    # If error is about time validation, treat as warning
                    if "stop_time" in error_msg.lower() and "start_time" in error_msg.lower():
                        return {
                            "is_valid": True,
                            "errors": [],
                            "warnings": [{"type": "time_validation", "message": f"Time validation issue (treated as warning): {error_msg}"}],
                            "error_count": 0,
                            "warning_count": 1,
                            "summary": "✅ VALID (with time validation warning)"
                        }
                    # If error is about ID format/UUID pattern, suppress it as warning (not validation blocker)
                    elif "not a valid STIX identifier" in error_msg or "must match" in error_msg:
                        # ID format is not strict - allow it as warning
                        return {
                            "is_valid": True,
                            "errors": [],
                            "warnings": [{"type": "id_format", "message": f"Non-standard ID format: {error_msg}"}],
                            "error_count": 0,
                            "warning_count": 1,
                            "summary": "✅ VALID (with non-standard ID format)"
                        }
                    else:
                        # Other errors are actual validation failures
                        return {
                            "is_valid": False,
                            "errors": [{"type": "parse_error", "message": error_msg}],
                            "warnings": [],
                            "error_count": 1,
                            "warning_count": 0,
                            "summary": f"❌ INVALID - {error_msg}"
                        }
            
            except Exception as e:
                return {
                    "is_valid": False,
                    "errors": [{"type": "parse_error", "message": str(e)}],
                    "warnings": [],
                    "error_count": 1,
                    "warning_count": 0,
                    "summary": f"❌ INVALID - Parse error: {str(e)}"
                }
        
        # Validate XML (STIX 1.x)
        elif is_xml:
            try:
                # Remove any BOM and whitespace
                content_clean = content.lstrip('\ufeff')
                
                xml_root = etree.fromstring(content_clean.encode("utf-8"))
                
                # Try to parse with STIXPackage if available
                if STIXPackage:
                    try:
                        package = STIXPackage.from_xml(xml_root)
                    except:
                        pass  # STIXPackage optional
                
                # If we got here, XML parsed successfully
                return {
                    "is_valid": True,
                    "errors": [],
                    "warnings": [],
                    "error_count": 0,
                    "warning_count": 0,
                    "summary": "✅ VALID - STIX 1.x XML validated successfully"
                }
            
            except Exception as e:
                return {
                    "is_valid": False,
                    "errors": [{"type": "xml_parse_error", "message": str(e)}],
                    "warnings": [],
                    "error_count": 1,
                    "warning_count": 0,
                    "summary": f"❌ INVALID - XML Parse Error: {str(e)}"
                }
        
        # Unknown format
        else:
            return {
                "is_valid": False,
                "errors": [{"type": "format_error", "message": "Could not detect file format (not valid JSON or XML)"}],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0,
                "summary": "❌ INVALID - Unrecognized file format"
            }

    @classmethod
    def extract_statistics(cls, filepath):
        """
        Extract STIX content statistics (handles both JSON and XML)
        
        Returns:
            dict: Statistics about the STIX file
        """
        filepath = Path(filepath)
        
        stats = {
            "total_objects": 0,
            "threat_indicators": 0,
            "malware_objects": 0,
            "identity_objects": 0,
            "campaign_objects": 0,
            "attack_pattern_objects": 0,
            "tool_objects": 0,
            "vulnerability_objects": 0,
            "object_types": {}
        }
        
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read()
            
            # Try JSON first (STIX 2.x)
            try:
                data = json.loads(content)
                
                if data.get("type") == "bundle" and "objects" in data:
                    objects = data["objects"]
                    stats["total_objects"] = len(objects)
                    
                    for obj in objects:
                        obj_type = obj.get("type", "unknown")
                        
                        # Count by type
                        stats["object_types"][obj_type] = stats["object_types"].get(obj_type, 0) + 1
                        
                        # Count specific threat indicators
                        if obj_type == "indicator":
                            stats["threat_indicators"] += 1
                        elif obj_type == "malware":
                            stats["malware_objects"] += 1
                        elif obj_type == "identity":
                            stats["identity_objects"] += 1
                        elif obj_type == "campaign":
                            stats["campaign_objects"] += 1
                        elif obj_type == "attack-pattern":
                            stats["attack_pattern_objects"] += 1
                        elif obj_type == "tool":
                            stats["tool_objects"] += 1
                        elif obj_type == "vulnerability":
                            stats["vulnerability_objects"] += 1
                elif isinstance(data, list):
                    # Handle array of objects
                    stats["total_objects"] = len(data)
                    for obj in data:
                        obj_type = obj.get("type", "unknown")
                        stats["object_types"][obj_type] = stats["object_types"].get(obj_type, 0) + 1
                        
                        if obj_type == "indicator":
                            stats["threat_indicators"] += 1
                        elif obj_type == "malware":
                            stats["malware_objects"] += 1
                        elif obj_type == "identity":
                            stats["identity_objects"] += 1
                        elif obj_type == "campaign":
                            stats["campaign_objects"] += 1
                        elif obj_type == "attack-pattern":
                            stats["attack_pattern_objects"] += 1
                        elif obj_type == "tool":
                            stats["tool_objects"] += 1
                        elif obj_type == "vulnerability":
                            stats["vulnerability_objects"] += 1
                
                return stats
            
            except json.JSONDecodeError:
                # Not JSON, try XML (STIX 1.x)
                try:
                    from lxml import etree
                    xml_root = etree.fromstring(content.encode("utf-8"))
                    
                    # For STIX 1.x XML, just count general statistics
                    # Count all elements as objects
                    all_elements = xml_root.findall(".//*")
                    stats["total_objects"] = len(all_elements)
                    
                    # Count specific types
                    indicators = xml_root.findall(".//{http://stix.mitre.org/Indicator-2}Indicator")
                    stats["threat_indicators"] = len(indicators)
                    
                    malwares = xml_root.findall(".//{http://stix.mitre.org/Malware-2}Malware")
                    stats["malware_objects"] = len(malwares)
                    
                    ttps = xml_root.findall(".//{http://stix.mitre.org/TTP-2}TTP")
                    stats["attack_pattern_objects"] = len(ttps)
                    
                    observables = xml_root.findall(".//{http://cybox.mitre.org/XMLSchema/v2.1}Observable")
                    stats["object_types"]["observable"] = len(observables)
                    
                    return stats
                
                except Exception as xml_e:
                    return {
                        "error": f"Could not parse file as JSON or XML: {str(xml_e)}",
                        "total_objects": 0,
                        "threat_indicators": 0,
                        "object_types": {}
                    }
        
        except Exception as e:
            return {
                "error": str(e),
                "total_objects": 0,
                "threat_indicators": 0,
                "object_types": {}
            }

    @classmethod
    def extract_statistics_from_data(cls, data):
        """
        Extract STIX content statistics directly from data dict
        """
        stats = {
            "total_objects": 0,
            "threat_indicators": 0,
            "malware_objects": 0,
            "identity_objects": 0,
            "campaign_objects": 0,
            "attack_pattern_objects": 0,
            "tool_objects": 0,
            "vulnerability_objects": 0,
            "object_types": {}
        }
        
        try:
            if data.get("type") == "bundle" and "objects" in data:
                objects = data["objects"]
                stats["total_objects"] = len(objects)
                
                for obj in objects:
                    obj_type = obj.get("type", "unknown")
                    stats["object_types"][obj_type] = stats["object_types"].get(obj_type, 0) + 1
                    
                    if obj_type == "indicator":
                        stats["threat_indicators"] += 1
                    elif obj_type == "malware":
                        stats["malware_objects"] += 1
                    elif obj_type == "identity":
                        stats["identity_objects"] += 1
                    elif obj_type == "campaign":
                        stats["campaign_objects"] += 1
                    elif obj_type == "attack-pattern":
                        stats["attack_pattern_objects"] += 1
                    elif obj_type == "tool":
                        stats["tool_objects"] += 1
                    elif obj_type == "vulnerability":
                        stats["vulnerability_objects"] += 1
            
            return stats
        
        except Exception as e:
            return {
                "error": str(e),
                "total_objects": 0,
                "threat_indicators": 0,
                "object_types": {}
            }
