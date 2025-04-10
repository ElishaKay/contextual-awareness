# meaning_engine.py
from plugins.therapist.plugin import analyze_therapist_context
from plugins.security.plugin import analyze_security_context
from plugins.personalization.plugin import analyze_personalization_context

class ContextualMeaningEngine:
    def __init__(self, mode="therapist"):
        self.mode = mode

    def analyze(self, user_input):
        # Get mode-specific analysis
        if self.mode == "therapist":
            analysis = analyze_therapist_context(user_input)
        elif self.mode == "security":
            analysis = analyze_security_context(user_input)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Add personalization analysis
        personalization = analyze_personalization_context(user_input)
        print(f"Personalization analysis: {personalization}")
        analysis["personalization"] = personalization
        return analysis
