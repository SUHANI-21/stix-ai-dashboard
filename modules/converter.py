"""
STIX Converter Module
Converts STIX 1.x and 2.0 to STIX 2.1
"""
import json
import sys
import subprocess
import tempfile
import os
from pathlib import Path
from uuid import uuid4

# Add source_code to path
source_code_path = Path(__file__).parent.parent.parent / "source_code"

try:
    from stix2 import parse as stix2_parse
except ImportError:
    stix2_parse = None


class STIXConverter:
    """Convert STIX files to version 2.1"""

    @classmethod
    def convert_to_2_1(cls, filepath, input_version, input_format):
        """
        Convert any STIX version to 2.1
        
        Args:
            filepath (str): Path to STIX file
            input_version (str): Detected version (1.x, 2.0, 2.1)
            input_format (str): Format (json or xml)
            
        Returns:
            dict: {
                'success': bool,
                'converted_data': dict or None,
                'message': str
            }
        """
        filepath = Path(filepath)
        
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "success": False,
                "converted_data": None,
                "message": f"Error reading file: {str(e)}"
            }
        
        # If already STIX 2.1, just return parsed
        if input_format == "json" and input_version and "2.1" in str(input_version):
            try:
                data = json.loads(content)
                return {
                    "success": True,
                    "converted_data": data,
                    "message": "Already STIX 2.1 - no conversion needed"
                }
            except Exception as e:
                return {
                    "success": False,
                    "converted_data": None,
                    "message": f"Error parsing STIX 2.1: {str(e)}"
                }
        
        # Convert STIX 1.x XML to 2.1
        if input_format == "xml" and input_version and "1." in str(input_version):
            return cls._convert_1x_to_2_1(str(filepath))
        
        # Convert STIX 2.0 JSON to 2.1
        if input_format == "json" and input_version and "2.0" in str(input_version):
            return cls._convert_2_0_to_2_1(content)
        
        return {
            "success": False,
            "converted_data": None,
            "message": f"Cannot convert: unsupported version {input_version} or format {input_format}"
        }

    @classmethod
    def _convert_1x_to_2_1(cls, filepath):
        """
        Convert STIX 1.x XML to STIX 2.1 JSON
        Runs in isolated subprocess to avoid lxml/stixmarx compatibility issues
        """
        try:
            # Create a standalone Python script to run conversion
            converter_code = """
import sys
import json
import traceback
import warnings

# Suppress all warnings to prevent stdout contamination
warnings.filterwarnings('ignore')

sys.path.insert(0, r'{source_code_path}')

# Fix lxml compatibility issue with stix2-elevator
try:
    import lxml.etree as etree
    if not hasattr(etree, '_ElementStringResult'):
        # Patch missing _ElementStringResult for lxml 5.0+ compatibility
        etree._ElementStringResult = str
except ImportError:
    pass

try:
    from stix2elevator import elevate
    from stix2elevator.options import initialize_options
    
    filepath = r'{filepath}'
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    # Initialize and convert
    initialize_options()
    result = elevate(xml_content)
    
    if result is None:
        print(json.dumps({{'success': False, 'error': 'elevate() returned None - conversion failed'}}))
        sys.exit(1)
    
    # Parse and output
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    
    data = json.loads(result)
    print(json.dumps({{'success': True, 'data': data}}))
    
except Exception as e:
    error_msg = f'{{type(e).__name__}}: {{str(e)}}'
    print(json.dumps({{'success': False, 'error': error_msg}}))
    sys.exit(1)
""".format(source_code_path=str(source_code_path), filepath=filepath)
            
            # Run in subprocess with clean environment
            result = subprocess.run(
                [sys.executable, "-c", converter_code],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_output = result.stderr if result.stderr else result.stdout
                return {
                    "success": False,
                    "converted_data": None,
                    "message": f"Conversion error: {error_output[:200]}"
                }
            
            # Parse result
            if not result.stdout.strip():
                return {
                    "success": False,
                    "converted_data": None,
                    "message": f"No output from conversion process. Error: {result.stderr}"
                }
            
            try:
                # Extract JSON from potentially contaminated output
                stdout_lines = result.stdout.strip()
                
                # Find the JSON part (starts with { and ends with })
                json_start = stdout_lines.find('{')
                if json_start == -1:
                    return {
                        "success": False,
                        "converted_data": None,
                        "message": f"No JSON found in output: {stdout_lines[:200]}"
                    }
                
                json_part = stdout_lines[json_start:]
                output = json.loads(json_part)
                
                if output.get("success"):
                    return {
                        "success": True,
                        "converted_data": output["data"],
                        "message": "✅ Successfully converted STIX 1.x to STIX 2.1"
                    }
                else:
                    return {
                        "success": False,
                        "converted_data": None,
                        "message": f"Conversion failed: {output.get('error', 'Unknown error')}"
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "converted_data": None,
                    "message": f"JSON parse error: {str(e)}. Output: {result.stdout[:200]}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "converted_data": None,
                "message": "Conversion timed out (>120s)"
            }
        except Exception as e:
            return {
                "success": False,
                "converted_data": None,
                "message": f"Conversion failed: {str(e)}"
            }

    @classmethod
    def _convert_2_0_to_2_1(cls, json_content):
        """Convert STIX 2.0 JSON to STIX 2.1"""
        try:
            if not stix2_parse:
                return {
                    "success": False,
                    "converted_data": None,
                    "message": "stix2 module not available"
                }
            
            # Parse with stix2 and it handles upgrade automatically
            obj = stix2_parse(json_content, allow_custom=True)
            
            # Serialize back to JSON
            converted_json = obj.serialize()
            converted_data = json.loads(converted_json)
            
            return {
                "success": True,
                "converted_data": converted_data,
                "message": "✅ Successfully converted STIX 2.0 to STIX 2.1"
            }
        
        except Exception as e:
            return {
                "success": False,
                "converted_data": None,
                "message": f"STIX 2.0 conversion error: {str(e)}"
            }
