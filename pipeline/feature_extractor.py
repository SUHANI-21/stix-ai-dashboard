def build_prompt(malware, bundle=None):
    """
    Build LLM prompt from malware object with specific features.
    
    Args:
        malware: dict with malware STIX object
        bundle: dict with full bundle (optional, for extracting relationships)
    
    Returns:
        str: Formatted prompt for LLM
    """
    
    # Extract specific features used in model training
    malware_id = malware.get("id", "")
    malware_name = malware.get("name", "")
    description = malware.get("description", "")
    aliases = malware.get("aliases", [])
    platforms = malware.get("platforms", [])
    is_family = malware.get("is_family", False)
    confidence = malware.get("confidence", 0)
    external_references = malware.get("external_references", [])
    
    # Count relationships if bundle is provided
    num_campaigns = 0
    num_intrusion_sets = 0
    num_tools = 0
    num_relationships = 0
    
    if bundle:
        for obj in bundle.get("objects", []):
            # Count relationship objects
            if obj.get("type") == "relationship":
                num_relationships += 1
                target_ref = obj.get("target_ref", "")
                if "campaign" in target_ref:
                    num_campaigns += 1
                elif "intrusion-set" in target_ref:
                    num_intrusion_sets += 1
                elif "tool" in target_ref:
                    num_tools += 1
    
    # Format aliases
    aliases_str = ", ".join(aliases) if aliases else "None"
    
    # Format platforms
    platforms_str = ", ".join(platforms) if platforms else "None"
    
    # Format external references summary
    refs_summary = ""
    if external_references:
        refs_summary = f"({len(external_references)} external references)"
    
    # Build structured feature text
    features_text = f"""
Malware ID: {malware_id}
Name: {malware_name}
Aliases: {aliases_str}
Is Family: {is_family}
Platforms: {platforms_str}
Confidence: {confidence}
Description: {description}
External References: {refs_summary}
Campaigns: {num_campaigns}
Intrusion Sets: {num_intrusion_sets}
Tools: {num_tools}
Total Relationships: {num_relationships}
"""
    
    prompt = f"""You are a cybersecurity analyst specializing in malware analysis and MITRE ATT&CK tactics.

Analyze the following malware and profile its likely attack techniques and behaviors:

{features_text}

Based on this malware profile, generate a detailed analysis including:
- Primary attack capabilities
- Likely MITRE ATT&CK techniques
- Behavioral patterns
- Command and control indicators
- Data exfiltration methods
- Persistence mechanisms
- Privilege escalation approaches
"""
    
    return prompt
