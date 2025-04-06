# schemas.py

# Defines the expected schema for memory storage formats
# This could be used for validation (if desired)

session_schema = {
    "emotion_trends": list,
    "intents": list,
    "topics": list,
    "turns": list
}

conversation_turn_schema = {
    "user": str,
    "bot": str
}
