# core/pipeline.py
import os
import json
import logging
from pymongo import MongoClient

# Import our personalization module
from core.personalization_context import fetch_personalization_context, save_personalization_context
from memory.memory_store import load_user_memory, save_user_memory

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Suppress logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

class TCAPipeline:
    def __init__(self, mode="therapist", session_id="default-user"):
        """
        Initialize core modules and store the session id.
        The session_id will be used for the persistent user record.
        """
        from core.memory_core import TemporalMemoryCore
        from core.meaning_engine import ContextualMeaningEngine
        from core.pattern_tracker import PatternShiftTracker
        from core.response_engine import AdaptiveResponseEngine

        self.mode = mode
        self.session_id = session_id
        self.user_id = os.environ.get("USER_ID", session_id)
        self.memory_core = TemporalMemoryCore(user_id=self.session_id)
        self.meaning_engine = ContextualMeaningEngine(mode, user_id=self.user_id)
        self.pattern_tracker = PatternShiftTracker()
        self.response_engine = AdaptiveResponseEngine(mode)
        self.turns = []  # Conversation history.
        self.components = {}
        
        # Load user memory from the memory store
        self.user_memory = load_user_memory(self.user_id)
        logger.debug(f"Loaded user memory for user_id: {self.user_id}")

    def load(self, checkpoint_state: dict):
        """
        Load the pipeline state from a checkpoint.
        """
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])
        self.components = checkpoint_state.get("components", {})
        logger.debug("Loaded checkpoint state: %s", 
                     json.dumps(checkpoint_state, indent=2, default=str))

    def load_personalization_context(self) -> dict:
        """
        Retrieve personalization context for the current session.
        """
        personalization_context = fetch_personalization_context(self.session_id)
        logger.debug("Personalization context loaded: %s", 
                     json.dumps(personalization_context, indent=2, default=str))
        return personalization_context

    def process(self, user_input: str) -> dict:
        """
        Process a single user input through several stages, including:
          - Analysis, conversation tracking and memory update.
          - Optional personalization updates if explicitly requested.
          - Update of the unified persistent user document via the memory core.
          - Generation of an adaptive response augmented with personalization.
        """
        # Step 1: Analyze user input.
        analysis = self.meaning_engine.analyze(user_input)
        logger.debug("Analysis: %s", json.dumps({"meaning_engine_analysis": analysis}, indent=2, default=str))
        
        # Step 2: Track conversation patterns.
        pattern = self.pattern_tracker.track(self.turns, analysis)
        logger.debug("Pattern tracking result: %s", json.dumps({"pattern_tracker_result": pattern}, indent=2, default=str))
        
        # Step 3: Update in-session memory.
        self.memory_core.update(analysis, pattern)
        
        # (Optional) Check if the user wants to update their profile.
        lower_input = user_input.lower()
        if "save in my profile" in lower_input:
            if "that" in lower_input:
                # Extract the text after "that"
                _, _, info_to_save = lower_input.partition("that")
                info_to_save = info_to_save.strip()
                if info_to_save:
                    # Save the info to the dedicated personalization store.
                    save_personalization_context(self.session_id, "profile", info_to_save)
                    logger.debug("Saved profile info: %s", info_to_save)
        
        # Step 4: Load personalization context.
        personalization_context = self.load_personalization_context()
        
        # Ensure that the value for "profile" is always a dictionary.
        profile_db = personalization_context.get("profile", {})
        if isinstance(profile_db, dict):
            profile_data = profile_db
        else:
            profile_data = {"info": profile_db}
        
        # Extract todos (convert each to string).
        todos_data = [str(item.get("todo")) for item in personalization_context.get("todos", []) if item.get("todo") is not None]

        # Now update the unified user context with the personalized data.
        self.memory_core.update_user_context(
            profile=profile_data,
            todos=todos_data,
            instructions=personalization_context.get("instructions", ""),
            research_goals=personalization_context.get("research_goals", "")
        )
        
        # Step 5: Build conversation history.
        conversation_history = self.turns[:]  # Shallow copy.
        conversation_history.append({"user": user_input, "bot": ""})
        
        # Step 6: Augment analysis with personalization context.
        augmented_analysis = analysis.copy()
        augmented_analysis["personalization_context"] = personalization_context

        # Step 7: Generate response
        response = self.response_engine.decide(augmented_analysis,
                                               self.memory_core.to_dict(),
                                               conversation_history)
        logger.debug("Adaptive response: %s", json.dumps({"adaptive_response": response}, indent=2, default=str))
        
        # Step 8: Update persistent memory.
        self.memory_core.append_turn(user_input, response.get("response"))
        self.turns.append({"user": user_input, "bot": response.get("response")})
        
        # Step 9: Update components
        self.components = {
            "last_analysis": analysis,
            "pattern": pattern,
            "memory_core": self.memory_core.to_dict(),
            "personalization_context": personalization_context
        }
        
        # Step 10: Save user memory
        self.user_memory.update({
            "last_interaction": {
                "input": user_input,
                "response": response.get("response"),
                "timestamp": analysis.get("timestamp", "")
            }
        })
        save_user_memory(self.user_id, self.user_memory)
        
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