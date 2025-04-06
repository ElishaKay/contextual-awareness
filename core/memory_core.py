# memory_core.py

class TemporalMemoryCore:
    def __init__(self):
        self.session_state = {
            "emotion_trends": [],
            "intents": [],
            "topics": [],
            "turns": []
        }

    def load(self, state_dict):
        if state_dict:
            self.session_state.update(state_dict)

    def update(self, analysis, pattern):
        self.session_state["emotion_trends"].append(analysis.get("emotion"))
        self.session_state["intents"].append(analysis.get("intent"))
        self.session_state["topics"].append(analysis.get("topic"))
        return self.session_state

    def append_turn(self, user_input, bot_response):
        self.session_state["turns"].append({"user": user_input, "bot": bot_response})

    def to_dict(self):
        return self.session_state
