# core/memory_core.py
"""
Module: core/memory_core.py

This module implements the TemporalMemoryCore class which maintains
in-memory session state and leverages MongoDB (with a Pydantic User model)
to store persistent user context.
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
        Initialize session state and persistent user context.
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
        Loads the user context from MongoDB. If no document exists for the given
        user_id, a new User record is created.
        """
        try:
            db = _get_mongo_db()
        except EnvironmentError as e:
            logger.warning("%s Returning default user context only.", e)
            return User(user_id=self.user_id)

        user_data = db["users"].find_one({"user_id": self.user_id})
        if user_data:
            try:
                # Convert MongoDB document to dict and remove _id field
                user_dict = dict(user_data)
                if "_id" in user_dict:
                    del user_dict["_id"]
                
                # Handle nested profile structure
                if "profile" in user_dict and isinstance(user_dict["profile"], dict):
                    # If profile has _id, remove it
                    if "_id" in user_dict["profile"]:
                        del user_dict["profile"]["_id"]
                    
                    # If profile has user_id, remove it (redundant)
                    if "user_id" in user_dict["profile"]:
                        del user_dict["profile"]["user_id"]
                
                # Ensure all required fields exist
                if "conversation_summary" not in user_dict:
                    user_dict["conversation_summary"] = ""
                if "last_summary_update" not in user_dict:
                    user_dict["last_summary_update"] = ""
                if "todos" not in user_dict:
                    user_dict["todos"] = []
                if "instructions" not in user_dict:
                    user_dict["instructions"] = ""
                if "research_goals" not in user_dict:
                    user_dict["research_goals"] = ""
                
                logger.debug(f"Loaded user context for user_id: {self.user_id}")
                return User(**user_dict)
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
        The "updated_at" field is always refreshed. For example:
        
            update_user_context(profile={"info": "Updated info"}, todos=["Buy milk"])
        """
        try:
            db = _get_mongo_db()
        except EnvironmentError as e:
            logger.warning("%s Cannot update user context.", e)
            return

        # Refresh the updated_at field
        kwargs["updated_at"] = self._get_current_timestamp()
        
        # Handle profile updates
        if "profile" in kwargs:
            if isinstance(kwargs["profile"], dict):
                # If profile is a dict, ensure it has the right structure
                if "info" not in kwargs["profile"] and "info" in self.user_context.profile:
                    # Preserve existing info if not provided
                    kwargs["profile"]["info"] = self.user_context.profile["info"]
            else:
                # If profile is a string, convert to dict with info field
                kwargs["profile"] = {"info": kwargs["profile"]}
        
        # Log the update for debugging
        logger.debug(f"Updating user context for user_id: {self.user_id} with data: {kwargs}")
        
        # Prepare the update document
        update_doc = {}
        for key, value in kwargs.items():
            if key == "profile" and isinstance(value, dict):
                # For profile, we need to update the nested fields
                for profile_key, profile_value in value.items():
                    update_doc[f"profile.{profile_key}"] = profile_value
            else:
                update_doc[key] = value
        
        # Perform the update
        update_result = db["users"].update_one(
            {"user_id": self.user_id},
            {"$set": update_doc},
            upsert=True,
        )
        if update_result.modified_count or update_result.upserted_id:
            logger.debug("User context updated for user_id: %s", self.user_id)
        else:
            logger.debug("No changes made to the user context for user_id: %s", self.user_id)
        
        # Reload the user context to ensure we have the latest data
        self.user_context = self.load_user_context()

    def update(self, analysis, pattern):
        """
        Update the transient session state based on analysis and pattern info.
        """
        # Add timestamp to the analysis
        if "timestamp" not in analysis:
            analysis["timestamp"] = self._get_current_timestamp()
            
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
        Export the current session state including the user context.
        """
        state = self.session_state.copy()
        state["user_context"] = self.user_context.dict()
        return state