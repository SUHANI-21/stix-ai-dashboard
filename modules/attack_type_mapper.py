def map_attack_type(technique_ids):
    ransomware_ids = {"T1486", "T1490"}
    phishing_ids = {"T1566"}
    credential_ids = {"T1003", "T1555"}
    lateral_ids = {"T1021", "T1570"}
    c2_ids = {"T1071", "T1105"}
    exfiltration_ids = {"T1041", "T1567"}

    categories = []

    for tid in technique_ids:
        if tid in ransomware_ids:
            categories.append("Ransomware Activity")
        elif tid in phishing_ids:
            categories.append("Phishing Attack")
        elif tid in credential_ids:
            categories.append("Credential Theft")
        elif tid in lateral_ids:
            categories.append("Lateral Movement")
        elif tid in c2_ids:
            categories.append("Command & Control Activity")
        elif tid in exfiltration_ids:
            categories.append("Data Exfiltration")

    if categories:
        return list(set(categories))
    else:
        return ["General Malicious Activity"]
