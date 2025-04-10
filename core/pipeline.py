# core/pipeline.py
import os
import json
import logging
from pymongo import MongoClient
from bson import ObjectId  # Import ObjectId if needed

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Suppress external libraries' logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

class TCAPipeline:
    def __init__(self, mode="therapist", session_id="default-user"):
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
        self.turns = []  # Conversation history
        self.components = {}  # Extra components state
        self.user_profile = {}  # User profile data

    def load(self, checkpoint_state: dict):
        """
        Load the pipeline state from a checkpoint dictionary.
        Converts any ObjectId elements to strings to ensure JSON serialization works.
        """
        self.memory_core.load(checkpoint_state.get("session_memory", {}))
        self.turns = checkpoint_state.get("turns", [])
        self.components = checkpoint_state.get("components", {})
        
        # Load user profile from session memory if available
        if "session_memory" in checkpoint_state and "user_profile" in checkpoint_state["session_memory"]:
            self.user_profile = checkpoint_state["session_memory"]["user_profile"]
            logger.info(f"Loaded user profile: {json.dumps(self.user_profile, indent=2)}")

        # Use default=str in json.dumps to automatically convert non-serializable types 
        logger.debug("Loaded checkpoint state: %s", 
                     json.dumps(checkpoint_state, indent=2, default=str))

    def load_personalization_context(self) -> dict:
        """
        Load personalization information from MongoDB.
        This includes the user profile, todos, instructions, and research goals.
        """
        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            logger.warning("MONGO_URI not set, skipping personalization context.")
            return {}
        client = MongoClient(mongo_uri)
        db = client["gptr_db"]
        session_id = self.session_id

        # Retrieve personalization data.
        profile = db["profile"].find_one({"user_id": session_id})
        todos = list(db["todos"].find({"user_id": session_id}))
        instructions_doc = db["instructions"].find_one({"user_id": session_id})
        research_goals_doc = db["research_goals"].find_one({"user_id": session_id})

        personalization_context = {
            "profile": profile if profile else {},
            "todos": todos,
            "instructions": instructions_doc.get("content") if instructions_doc else "",
            "research_goals": research_goals_doc.get("goals") if research_goals_doc else ""
        }
        logger.debug("Personalization context loaded: %s", json.dumps(personalization_context, indent=2, default=str))
        return personalization_context

    def process(self, user_input: str) -> dict:
        """
        Process a single user input through various stages:
          - Analysis via Meaning Engine,
          - Pattern tracking,
          - Updating memory,
          - Response generation.
        Personalization context is injected before generating a response.
        """
        # Step 1: Analyze the input using the Meaning Engine.
        analysis = self.meaning_engine.analyze(user_input)
        logger.debug("Analysis: %s", json.dumps({"meaning_engine_analysis": analysis}, indent=2, default=str))
        
        # Step 2: Track any shifts in conversation context.
        pattern = self.pattern_tracker.track(self.turns, analysis)
        logger.debug("Pattern tracking result: %s", json.dumps({"pattern_tracker_result": pattern}, indent=2, default=str))
        
        # Step 3: Update memory with analysis details.
        self.memory_core.update(analysis, pattern)
        
        # Step 4: Load personalization context from MongoDB.
        personalization_context = self.load_personalization_context()

        # Step 5: Build conversation history.
        conversation_history = self.turns[:]  # Shallow copy.
        conversation_history.append({"user": user_input, "bot": ""})
        
        # Step 6: Create augmented analysis including personalization details.
        augmented_analysis = analysis.copy()
        augmented_analysis["personalization_context"] = personalization_context

        response = self.response_engine.decide(augmented_analysis,
                                               self.memory_core.to_dict(),
                                               conversation_history)
        logger.debug("Adaptive response: %s", json.dumps({"adaptive_response": response}, indent=2, default=str))
        
        # Step 7: Update persistent memory and conversation turns.
        self.memory_core.append_turn(user_input, response.get("response"))
        self.turns.append({"user": user_input, "bot": response.get("response")})
        
        # Step 8: Check for profile updates in the response
        profile_updates = {}
        if "profile_updates" in response:
            profile_updates = response["profile_updates"]
            logger.info(f"Profile updates detected: {json.dumps(profile_updates, indent=2)}")
            
            # Update the user profile in memory
            self.user_profile.update(profile_updates)
            logger.info(f"Updated user profile: {json.dumps(self.user_profile, indent=2)}")
            
            # Add profile updates to the response for external handling
            response["profile_updates"] = profile_updates
        
        # Step 9: Update components with extra information if needed.
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
        # Ensure user_profile is included in session_memory
        session_memory = self.memory_core.to_dict()
        session_memory["user_profile"] = self.user_profile
        
        return {
            "session_memory": session_memory,
            "turns": self.turns,
            "components": self.components,
        }