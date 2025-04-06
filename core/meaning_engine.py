# meaning_engine.py
from plugins.therapist.plugin import analyze_therapist_context
from plugins.security.plugin import analyze_security_context

class ContextualMeaningEngine:
    def __init__(self, mode="therapist"):
        self.mode = mode

    def analyze(self, user_input):
        if self.mode == "therapist":
            return analyze_therapist_context(user_input)
        elif self.mode == "security":
            return analyze_security_context(user_input)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
