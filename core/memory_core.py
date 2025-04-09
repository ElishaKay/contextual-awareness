"""
Module: core/memory_core.py

This module implements the TemporalMemoryCore class which maintains
the in-memory session state (emotion trends, intents, topics, and conversation
turns) and leverages MongoDB (with a Pydantic User model) to store persistent user context.
"""

import os
import logging
from datetime import datetime
from pymongo import MongoClient

from memory.mongodb.schema import User  # Pydantic model

logger = logging.getLogger(__name__)

def _get_mongo_db():
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise EnvironmentError("MONGO_URI not set")
    client = MongoClient(mongo_uri)
    return client["gptr_db"]

class TemporalMemoryCore:
    def __init__(self, user_id: str = "default-user"):
        """
        Initialize the memory core with session state and persistent user context.
        
        session_state contains:
          - "emotion_trends": List of emotions over time.
          - "intents":        List of recognized intents.
          - "topics":         List of topics.
          - "turns":          List of conversation turns.
          
        Additionally, the user context document is loaded from MongoDB using
        the Pydantic User model. If the user record is not found, a default one is created.
        """
        self.session_state = {
            "emotion_trends": [],
            "intents": [],
            "topics": [],
            "turns": []
        }
        self.user_id = user_id
        self.user_context = self.load_user_context()

    def load(self, state_dict):
        """
        Load session state from a checkpoint.
        """
        if state_dict:
            self.session_state.update(state_dict)

    def _get_current_timestamp(self) -> str:
        return datetime.utcnow().isoformat()

    def load_user_context(self) -> User:
        """
        Loads the user context from the "users" collection in MongoDB, returning a User instance.
        If no document exists for the given user_id, a new User record is created.
        """
        try:
            db = _get_mongo_db()
        except EnvironmentError as e:
            logger.warning("%s Returning default user context only.", e)
            return User(user_id=self.user_id)

        user_data = db["users"].find_one({"user_id": self.user_id})
        if user_data:
            try:
                return User(**user_data)
            except Exception as e:
                logger.error("Error parsing user data with Pydantic: %s", e)
                return User(user_id=self.user_id)
        else:
            # New user: create default User model and store it.
            new_user = User(user_id=self.user_id)
            db["users"].insert_one(new_user.dict())
            return new_user

    def update_user_context(self, **kwargs):
        """
        Update the user context stored in MongoDB.
        Accepts keyword arguments corresponding to fields defined in the User model.
        For example:
        
            update_user_context(profile={"info": "New profile info"})
            update_user_context(todos=["Buy milk"])  # to set the todos field
        
        The "updated_at" field is always refreshed.
        After updating, the in-memory user_context is reloaded.
        """
        try:
            db = _get_mongo_db()
        except EnvironmentError as e:
            logger.warning("%s Cannot update user context.", e)
            return

        # Ensure updated_at is refreshed
        kwargs["updated_at"] = self._get_current_timestamp()
        update_result = db["users"].update_one(
            {"user_id": self.user_id},
            {"$set": kwargs},
            upsert=True,
        )
        if update_result.modified_count or update_result.upserted_id:
            logger.debug("User context updated for user_id: %s", self.user_id)
        else:
            logger.debug("No changes made to the user context for user_id: %s", self.user_id)
        self.user_context = self.load_user_context()

    def update(self, analysis, pattern):
        """
        Update the transient session state based on analysis and pattern info.
        """
        self.session_state["emotion_trends"].append(analysis.get("emotion"))
        self.session_state["intents"].append(analysis.get("intent"))
        self.session_state["topics"].append(analysis.get("topic"))
        return self.session_state

    def append_turn(self, user_input, bot_response):
        """
        Append a conversation turn to the session state.
        """
        self.session_state["turns"].append({"user": user_input, "bot": bot_response})

    def to_dict(self):
        """
        Export the current session state including the user context (converted to dict).
        """
        state = self.session_state.copy()
        state["user_context"] = self.user_context.dict()  # convert Pydantic model to dict
        return state