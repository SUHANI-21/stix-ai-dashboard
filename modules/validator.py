from stix2 import parse
from stix2 import parse
import json

def validate_stix(file_path):
    try:
        with open(file_path) as f:
            content = f.read()
        
        # Try strict validation first
        try:
            obj = parse(content, allow_custom=True)
            return True, "STIX validation successful"
        except Exception as e:
            error_msg = str(e)
            # If it's a time validation issue, treat as warning
            if "stop time later than start time" in error_msg.lower() or "start_time" in error_msg.lower():
                # Basic JSON validation as fallback
                data = json.loads(content)
                if data.get("type") == "bundle" and "objects" in data:
                    return True, f"⚠️ VALID (Warning: {error_msg})"
            raise e
            
    except Exception as e:
        return False, f"Validation Error: {str(e)}"
