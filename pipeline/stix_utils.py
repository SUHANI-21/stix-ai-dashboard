def extract_malware_object(bundle):
    """Extract the first malware object from a STIX bundle."""
    for obj in bundle.get("objects", []):
        if obj.get("type") == "malware":
            return obj
