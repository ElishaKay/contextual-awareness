# core/pipeline.py
import os
import json
import logging
from pymongo import MongoClient

# Import our new personalization module
from core.personalization_context import fetch_personalization_context, save_personalization_context

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Reduce log spam from external libraries.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

class TCAPipeline:
    def __init__(self, mode="therapist", session_id="default-user"):
        """
        Initialize core modules as before, but also store the session id.
        """
        from core.memory_core import TemporalMemoryCore
        from core.meaning_engine import ContextualMeaningEngine
        from core.pattern_tracker import PatternShiftTracker
        from core.response_engine import AdaptiveResponseEngine

        self.mode = mode
        self.session_id = session_id
        self.memory_core = TemporalMemoryCore()
        self.meaning_engine = ContextualMeaningEngine(mode)
        self.pattern_tracker = PatternShiftTracker()
        self.response_engine = AdaptiveResponseEngine(mode)
        self.turns = []  # Conversation history.
        self.components = {}

    def load(self, checkpoint_state: dict):
        """
        Load the pipeline state from a checkpoint dictionary.
        Converts any MongoDB ObjectId elements using default=str for JSON serialization.
        """
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])
        self.components = checkpoint_state.get("components", {})
        logger.debug("Loaded checkpoint state: %s", 
                     json.dumps(checkpoint_state, indent=2, default=str))

    def load_personalization_context(self) -> dict:
        """
        Delegate fetching of personalization context to the new module.
        """
        personalization_context = fetch_personalization_context(self.session_id)
        logger.debug("Personalization context loaded: %s", 
                     json.dumps(personalization_context, indent=2, default=str))
        return personalization_context

    def process(self, user_input: str) -> dict:
        """
        Process a single user input through various stages:
          - Analyze via the Meaning Engine.
          - Track conversation patterns.
          - Update memory.
          - Optionally update personalization context if the user is saving data.
          - Generate a response augmented with personalization context.
          - Update conversation history.
        """
        # Step 1: Analyze user input.
        analysis = self.meaning_engine.analyze(user_input)
        logger.debug("Analysis: %s", json.dumps({"meaning_engine_analysis": analysis}, indent=2, default=str))
        
        # Step 2: Track changes in conversation pattern.
        pattern = self.pattern_tracker.track(self.turns, analysis)
        logger.debug("Pattern tracking result: %s", json.dumps({"pattern_tracker_result": pattern}, indent=2, default=str))
        
        # Step 3: Update memory with analysis details.
        self.memory_core.update(analysis, pattern)
        
        # --- New Hook: Check if the user intends to update their profile ---
        # For example: "save in my profile that I like coding and chillig on the beach"
        if "save in my profile" in user_input.lower():
            lower_input = user_input.lower()
            if "that" in lower_input:
                # Extract text following "that"
                _, _, info_to_save = lower_input.partition("that")
                info_to_save = info_to_save.strip()
                if info_to_save:
                    save_personalization_context(self.session_id, "profile", info_to_save)
                    logger.debug("Saved profile info: %s", info_to_save)
        
        # Step 4: Load personalization context via our dedicated module.
        personalization_context = self.load_personalization_context()

        # Step 5: Build conversation history.
        conversation_history = self.turns[:]  # Shallow copy.
        conversation_history.append({"user": user_input, "bot": ""})
        
        # Step 6: Augment analysis with the personalization context.
        augmented_analysis = analysis.copy()
        augmented_analysis["personalization_context"] = personalization_context

        response = self.response_engine.decide(augmented_analysis,
                                               self.memory_core.to_dict(),
                                               conversation_history)
        logger.debug("Adaptive response: %s", json.dumps({"adaptive_response": response}, indent=2, default=str))
        
        # Step 7: Update persistent memory and conversation history.
        self.memory_core.append_turn(user_input, response.get("response"))
        self.turns.append({"user": user_input, "bot": response.get("response")})
        
        self.components = {
            "last_analysis": analysis,
            "pattern": pattern,
            "memory_core": self.memory_core.to_dict(),
            "personalization_context": personalization_context
        }
        return response

    def to_dict(self) -> dict:
        """
        Export the current state of the pipeline.
        """
        return {
            "session_memory": self.memory_core.to_dict(),
            "turns": self.turns,
            "components": self.components,
        }