"""
Generate malware descriptions from extracted STIX features.
Used as fallback when LLM is unavailable or times out.
"""


def generate_description_from_features(malware, bundle=None):
    """
    Generate a synthetic malware profile description from structured features.
    
    Args:
        malware: dict with malware STIX object
        bundle: dict with full bundle (optional, for relationship context)
    
    Returns:
        str: Generated description text suitable for model input
    """
    
    # Extract features
    name = malware.get("name", "Unknown")
    aliases = malware.get("aliases", [])
    description = malware.get("description", "")
    platforms = malware.get("platforms", [])
    is_family = malware.get("is_family", False)
    confidence = malware.get("confidence", 0)
    malware_types = malware.get("malware_types", [])
    
    # Count relationships if bundle provided
    num_campaigns = 0
    num_intrusion_sets = 0
    num_tools = 0
    num_relationships = 0
    
    if bundle:
        for obj in bundle.get("objects", []):
            if obj.get("type") == "relationship":
                num_relationships += 1
                target_ref = obj.get("target_ref", "")
                if "campaign" in target_ref:
                    num_campaigns += 1
                elif "intrusion-set" in target_ref:
                    num_intrusion_sets += 1
                elif "tool" in target_ref:
                    num_tools += 1
    
    # Build description from features
    parts = []
    
    # Core identity
    parts.append(f"Malware: {name}")
    
    if aliases:
        parts.append(f"Also known as: {', '.join(aliases)}")
    
    # Classification
    if is_family:
        parts.append("This is a malware family")
    
    if malware_types:
        parts.append(f"Type: {', '.join(malware_types)}")
    
    if platforms:
        parts.append(f"Target platforms: {', '.join(platforms)}")
    
    # Confidence and prevalence
    if confidence > 0:
        parts.append(f"Confidence level: {confidence}%")
    
    # Relationships and reach
    if num_campaigns > 0:
        parts.append(f"Used in {num_campaigns} campaign(s)")
    
    if num_intrusion_sets > 0:
        parts.append(f"Associated with {num_intrusion_sets} intrusion set(s)")
    
    if num_tools > 0:
        parts.append(f"Linked to {num_tools} tool(s)")
    
    if num_relationships > 0:
        parts.append(f"Part of {num_relationships} relationship(s)")
    
    # Original description if available
    if description:
        parts.append(f"Description: {description}")
    
    # Combine into full text
    generated = " ".join(parts)
    
    return generated
