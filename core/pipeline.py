# core/pipeline.py
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

class TCAPipeline:
    def __init__(self, mode="therapist"):
        # Import processing components.
        from core.memory_core import TemporalMemoryCore
        from core.meaning_engine import ContextualMeaningEngine
        from core.pattern_tracker import PatternShiftTracker
        from core.response_engine import AdaptiveResponseEngine

        self.mode = mode
        self.memory_core = TemporalMemoryCore()
        self.meaning_engine = ContextualMeaningEngine(mode)
        self.pattern_tracker = PatternShiftTracker()
        self.response_engine = AdaptiveResponseEngine(mode)

        # Conversation turns and extra checkpoint components.
        self.turns = []
        self.components = {}

    def load(self, checkpoint_state: dict):
        """
        Load the pipeline state from a checkpoint dictionary.
        """
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])
        self.components = checkpoint_state.get("components", {})
        logger.debug("Loaded checkpoint state: %s", json.dumps(checkpoint_state, indent=2))

    def process(self, user_input: str) -> dict:
        """
        Process a single user input through various stages:
          - analysis via meaning engine,
          - pattern tracking,
          - updating memory,
          - generating a response.
        """
        analysis = self.meaning_engine.analyze(user_input)
        pattern = self.pattern_tracker.track(self.turns, analysis)
        self.memory_core.update(analysis, pattern)
        response = self.response_engine.decide(analysis, self.memory_core.to_dict(), self.turns or [])
        
        # Append the conversation turn.
        self.memory_core.append_turn(user_input, response.get("response"))
        self.turns.append({"user": user_input, "bot": response.get("response")})
        
        # Update extra components (example).
        self.components = {
            "last_analysis": analysis,
            "pattern": pattern,
            "memory_core": self.memory_core.to_dict()
        }
        return response

    def to_dict(self) -> dict:
        """
        Export the pipeline checkpoint state for persistence.
        """
        return {
            "session_memory": self.memory_core.to_dict(),
            "turns": self.turns,
            "components": self.components
        }