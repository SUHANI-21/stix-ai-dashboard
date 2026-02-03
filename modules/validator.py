from stix2 import parse

def validate_stix(file_path):
    try:
        with open(file_path) as f:
            content = f.read()

        obj = parse(content, allow_custom=True)
        return True, "STIX validation successful"
    except Exception as e:
        return False, f"Validation Error: {str(e)}"
