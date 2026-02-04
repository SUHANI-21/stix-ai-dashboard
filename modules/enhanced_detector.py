"""
Enhanced STIX Version and Format Detector
Wraps the original VersionChecker with additional metadata
"""
import json
from pathlib import Path
from lxml import etree
from stix2 import parse as stix2_parse
from stix2.exceptions import STIXError

try:
    from stix.core import STIXPackage
except ImportError:
    STIXPackage = None


class EnhancedVersionChecker:
    """Enhanced version detection with detailed metadata"""

    @classmethod
    def detect_stix_full(cls, filepath):
        """
        Detect STIX version, format, and provide extended metadata
        
        Args:
            filepath (str): Path to STIX file
            
        Returns:
            dict: {
                'version': str,
                'format': str,
                'is_bundle': bool,
                'object_count': int,
                'file_size_kb': float,
                'is_valid': bool,
                'errors': list
            }
        """
        filepath = Path(filepath)
        errors = []
        
        try:
            # Get file size
            file_size_kb = filepath.stat().st_size / 1024
        except Exception as e:
            file_size_kb = 0
            errors.append(f"File size error: {str(e)}")
        
        # Read file with proper encoding
        try:
            with filepath.open("r", encoding="utf-8") as f:
                raw_data = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with filepath.open("r", encoding="latin-1") as f:
                    raw_data = f.read()
            except Exception as e:
                return {
                    "version": "Unknown",
                    "format": "Unknown",
                    "is_bundle": False,
                    "object_count": 0,
                    "file_size_kb": file_size_kb,
                    "is_valid": False,
                    "errors": [f"Encoding error: {str(e)}"]
                }
        except Exception as e:
            return {
                "version": "Unknown",
                "format": "Unknown",
                "is_bundle": False,
                "object_count": 0,
                "file_size_kb": file_size_kb,
                "is_valid": False,
                "errors": [f"File read error: {str(e)}"]
            }
        
        # Clean the content
        raw_data_clean = raw_data.lstrip('\ufeff').strip()
        
        # Try JSON first (STIX 2.x)
        if raw_data_clean.startswith('{') or raw_data_clean.startswith('['):
            try:
                # First, parse as dict to check structure
                data_dict = json.loads(raw_data_clean)
                
                # Then parse with stix2 for proper object handling
                try:
                    obj = stix2_parse(raw_data_clean, allow_custom=True)
                except:
                    pass  # stix2_parse optional
                
                spec_version = None
                is_bundle = False
                object_count = 0
                
                # Check if it's a bundle (from dict structure)
                if data_dict.get("type") == "bundle":
                    is_bundle = True
                    # Get object count from dict
                    objects = data_dict.get("objects", [])
                    object_count = len(objects)
                    # Get spec_version from first object that has it, or from bundle
                    spec_version = data_dict.get("spec_version")
                    if not spec_version and objects:
                        for inner_obj in objects:
                            spec_version = inner_obj.get("spec_version")
                            if spec_version:
                                break
                else:
                    # Single STIX object (not a bundle)
                    is_bundle = False
                    object_count = 1
                    spec_version = data_dict.get("spec_version")
                
                return {
                    "version": spec_version,
                    "format": "json",
                    "is_bundle": is_bundle,
                    "object_count": object_count,
                    "file_size_kb": file_size_kb,
                    "is_valid": True,
                    "errors": []
                }
            except (json.JSONDecodeError, STIXError) as e:
                errors.append(f"JSON parse error: {str(e)}")
        
        # Try XML (STIX 1.x)
        if raw_data_clean.startswith('<'):
            try:
                xml_root = etree.fromstring(raw_data_clean.encode("utf-8"))
                
                # Try to parse with STIXPackage if available
                if STIXPackage:
                    try:
                        package = STIXPackage.from_xml(xml_root)
                    except:
                        pass  # STIXPackage optional
                
                stix_version = xml_root.attrib.get("version")
                
                # Count objects in package - be lenient with element counting
                object_count = len(xml_root.findall(".//*"))
                
                return {
                    "version": stix_version,
                    "format": "xml",
                    "is_bundle": True,
                    "object_count": object_count,
                    "file_size_kb": file_size_kb,
                    "is_valid": True,
                    "errors": []
                }
            except Exception as e:
                errors.append(f"XML parse error: {str(e)}")
        
        # If all parsing fails
        return {
            "version": "Unknown",
            "format": "Unknown",
            "is_bundle": False,
            "object_count": 0,
            "file_size_kb": file_size_kb,
            "is_valid": False,
            "errors": errors
        }
