# plugin.py (Therapist Plugin)
import random

def analyze_therapist_context(user_input):
    if "tired" in user_input or "exhausted" in user_input:
        emotion = "fatigue"
    elif "not good enough" in user_input or "worthless" in user_input:
        emotion = "low self-worth"
    else:
        emotion = random.choice(["anxious", "overwhelmed", "neutral"])

    if "want to" in user_input or "wish I" in user_input:
        intent = "goal_expression"
    elif "can't" in user_input or "don't know" in user_input:
        intent = "confusion"
    else:
        intent = "emotional_disclosure"

    return {
        "intent": intent,
        "emotion": emotion,
        "topic": "personal struggle",
        "tone": "vulnerable"
    }
