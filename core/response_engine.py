# response_engine.py

class AdaptiveResponseEngine:
    def __init__(self, mode="therapist"):
        self.mode = mode

    def decide(self, analysis, memory_state):
        if self.mode == "therapist":
            return self._therapist_response(analysis, memory_state)
        elif self.mode == "security":
            return self._security_response(analysis)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _therapist_response(self, analysis, memory_state):
        emotion = analysis.get("emotion")
        intent = analysis.get("intent")

        if emotion == "fatigue":
            return {"response": "That sounds really draining. What’s been making you feel this way lately?", "mode": "comforting"}
        elif emotion == "low self-worth":
            return {"response": "That belief can be so heavy. Want to explore where it comes from?", "mode": "reflective"}
        elif intent == "goal_expression":
            return {"response": "That’s a powerful goal. What’s one small way we could move toward it?", "mode": "encouraging"}
        else:
            return {"response": "I'm here and listening—tell me more about what’s going on.", "mode": "neutral"}

    def _security_response(self, analysis):
        risk = analysis.get("risk_level")
        if risk == "high":
            return {"response": "This request violates safety protocols and cannot be processed.", "mode": "block"}
        elif risk == "medium":
            return {"response": "That topic could lead to unsafe outcomes. Please rephrase.", "mode": "warn"}
        else:
            return {"response": "Your request is within acceptable bounds. How can I assist further?", "mode": "allow"}
