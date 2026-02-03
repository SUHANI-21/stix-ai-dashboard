def assess_credibility(confidence, threat_probability):
    score = (0.6 * confidence) + (0.4 * threat_probability)

    if score >= 80:
        level = "High Trust"
    elif score >= 50:
        level = "Medium Trust"
    else:
        level = "Low Trust"

    return round(score, 2), level
