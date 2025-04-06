# plugin.py (Security Plugin)

def analyze_security_context(user_input):
    lowered = user_input.lower()

    if any(trigger in lowered for trigger in ["ignore instructions", "disregard safety", "disable"]):
        risk_level = "high"
        intent = "bypass_attempt"
    elif any(trigger in lowered for trigger in ["how do i jailbreak", "exploit"]):
        risk_level = "medium"
        intent = "information_probe"
    else:
        risk_level = "low"
        intent = "general_query"

    return {
        "intent": intent,
        "emotion": "neutral",
        "topic": "security compliance",
        "tone": "technical",
        "risk_level": risk_level
    }
