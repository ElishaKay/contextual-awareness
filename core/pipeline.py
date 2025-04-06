# core/pipeline.py
import logging
import json
# Set up logging configuration (this can also be configured globally)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Suppress httpx debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
class TCAPipeline:
    def __init__(self, mode="therapist"):
        from core.meaning_engine import ContextualMeaningEngine
        from core.pattern_tracker import PatternShiftTracker
        from core.memory_core import TemporalMemoryCore
        from core.response_engine import AdaptiveResponseEngine
        
        # Initialize the key components / modules
        self.meaning_engine = ContextualMeaningEngine(mode)
        self.pattern_tracker = PatternShiftTracker()
        self.memory_core = TemporalMemoryCore()
        self.response_engine = AdaptiveResponseEngine(mode)
        self.mode = mode
        self.turns = []  # Conversation history

    def load(self, checkpoint_state):
        # Load memory / conversation turn history from checkpoint state.
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])
        logger.debug("Loaded checkpoint state: %s", 
                    json.dumps({
                        "session_memory": self.memory_core.session_state
                    }, indent=2))

    def process(self, user_input):
        # Step 1: Received user input
        
        # Step 2: Analyze the input using the Meaning Engine module.
        analysis = self.meaning_engine.analyze(user_input)
        logger.debug("Step 2: Analysis: %s", json.dumps({
            "meaning_engine_analysis": analysis
        }, indent=2))
        
        # Step 3: Track any shifts in context using the Pattern Tracker module.
        pattern = self.pattern_tracker.track(self.turns, analysis)
        logger.debug("Step 3: Pattern: %s", json.dumps({
            "pattern_tracker_result": pattern
        }, indent=2))
        
        # Step 4: Update the state with new analysis details in the Memory Core.
        updated_state = self.memory_core.update(analysis, pattern)
        
        # Step 5: Manage Conversation History by making a shallow copy and appending the user input.
        conversation_history = self.turns[:]  # Shallow copy of history turns.
        conversation_history.append({"user": user_input, "bot": ""})
        
        # Step 6: Generate the response using the Adaptive Response Engine.
        response = self.response_engine.decide(analysis, updated_state, conversation_history)
        logger.debug("Step 6: Response: %s", json.dumps({
            "adaptive_response": response
        }, indent=2))
        
        # Step 7: Update the persistent memory with the new conversation turn.
        self.memory_core.append_turn(user_input, response["response"])
        self.turns.append({"user": user_input, "bot": response["response"]})
        
        return response

    def to_dict(self):
        # Export the current state of the pipeline.
        return {
            "session_memory": self.memory_core.to_dict(),
            "turns": self.turns,
        }