# pipeline.py
from core.meaning_engine import ContextualMeaningEngine
from core.pattern_tracker import PatternShiftTracker
from core.memory_core import TemporalMemoryCore
from core.response_engine import AdaptiveResponseEngine

class TCAPipeline:
    def __init__(self, mode="therapist"):
        self.meaning_engine = ContextualMeaningEngine(mode)
        self.pattern_tracker = PatternShiftTracker()
        self.memory_core = TemporalMemoryCore()
        self.response_engine = AdaptiveResponseEngine(mode)
        self.mode = mode

    def load(self, checkpoint_state):
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])

    def process(self, user_input):
        analysis = self.meaning_engine.analyze(user_input)
        pattern = self.pattern_tracker.track(self.turns, analysis)
        updated_state = self.memory_core.update(analysis, pattern)
        
        # Build the conversation history from the previous turns
        conversation_history = self.turns[:]  # Make a copy of existing conversation history.
        conversation_history.append({"user": user_input, "bot": ""})  # Append the current user input.
        
        response = self.response_engine.decide(analysis, updated_state, conversation_history)
        
        self.memory_core.append_turn(user_input, response["response"])
        self.turns.append({"user": user_input, "bot": response["response"]})
        
        return response

    def to_dict(self):
        return {
            "session_memory": self.memory_core.to_dict(),
            "turns": self.turns
        }
