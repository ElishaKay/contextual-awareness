"""
Module: core/personalization_context.py

This module handles operations for fetching and saving a user's personalization context.
It works with the following collections:
    - "profile"        (stores a document keyed by user_id)
    - "todos"          (stores individual todo records keyed by user_id)
    - "instructions"   (stores a document with a "content" field, keyed by user_id)
    - "research_goals" (stores a document with a "goals" field, keyed by user_id)
"""

import os
import logging
from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

def _get_mongo_db():
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise EnvironmentError("MONGO_URI not set")
    client = MongoClient(mongo_uri)
    return client["gptr_db"]

def fetch_personalization_context(session_id: str) -> dict:
    """
    Retrieve the personalization context from MongoDB for a given session_id.
    Returns a dictionary with keys: "profile", "todos", "instructions", "research_goals".
    """
    try:
        db = _get_mongo_db()
        
        # Fetch the user document from the users collection
        user_doc = db["users"].find_one({"user_id": session_id})
        
        if user_doc:
            # Extract profile information
            profile = user_doc.get("profile", {})
            if isinstance(profile, dict):
                # If profile is a dict, extract the info field
                profile_info = profile.get("info", "")
            else:
                # If profile is a string, use it directly
                profile_info = profile
                
            # Extract other fields
            todos = user_doc.get("todos", [])
            instructions = user_doc.get("instructions", "")
            research_goals = user_doc.get("research_goals", "")
            
            context = {
                "profile": {"info": profile_info},
                "todos": todos,
                "instructions": instructions,
                "research_goals": research_goals
            }
            
            logger.debug(f"Fetched personalization context for session_id: {session_id}")
            return context
        else:
            logger.debug(f"No user document found for session_id: {session_id}")
            return {"profile": {}, "todos": [], "instructions": "", "research_goals": ""}
            
    except Exception as e:
        logger.error(f"Error fetching personalization context: {e}")
        # Return empty context on error
        return {"profile": {}, "todos": [], "instructions": "", "research_goals": ""}

def save_personalization_context(session_id: str, field: str, value: str):
    """
    Save (or update) a personalization field for the given session_id.

    Allowed fields:
      - "profile":       A string containing user's profile info.
      - "instructions":  A string for the instructions collection.
      - "research_goals": A string for the research_goals collection.
      - "todos":         A todo item (each todo is inserted as a separate record).

    All data is saved to the users collection.
    """
    try:
        db = _get_mongo_db()
        now = datetime.utcnow().isoformat()

        # Get the current user document
        user_doc = db["users"].find_one({"user_id": session_id})
        
        if field == "profile":
            if user_doc:
                # Get the current profile
                current_profile = user_doc.get("profile", {})
                if isinstance(current_profile, dict):
                    current_info = current_profile.get("info", "")
                else:
                    current_info = current_profile
                
                # Append new information if it's not already present
                if value not in current_info:
                    updated_info = (current_info + " " + value).strip()
                    db["users"].update_one(
                        {"user_id": session_id},
                        {"$set": {"profile.info": updated_info, "updated_at": now}}
                    )
                    logger.debug(f"Updated profile for session_id: {session_id} with value: {value}")
            else:
                # Create a new user document
                db["users"].insert_one({
                    "user_id": session_id,
                    "profile": {"info": value},
                    "created_at": now,
                    "updated_at": now
                })
                logger.debug(f"Created new profile for session_id: {session_id} with value: {value}")
        elif field == "instructions":
            db["users"].update_one(
                {"user_id": session_id},
                {"$set": {"instructions": value, "updated_at": now}},
                upsert=True
            )
            logger.debug(f"Updated instructions for session_id: {session_id} with value: {value}")
        elif field == "research_goals":
            db["users"].update_one(
                {"user_id": session_id},
                {"$set": {"research_goals": value, "updated_at": now}},
                upsert=True
            )
            logger.debug(f"Updated research_goals for session_id: {session_id} with value: {value}")
        elif field == "todos":
            # For todos, we need to append to the existing list
            if user_doc and "todos" in user_doc:
                current_todos = user_doc["todos"]
                if value not in current_todos:
                    current_todos.append(value)
                    db["users"].update_one(
                        {"user_id": session_id},
                        {"$set": {"todos": current_todos, "updated_at": now}}
                    )
                    logger.debug(f"Updated todos for session_id: {session_id} with value: {value}")
            else:
                # Create a new user document with the todo
                db["users"].update_one(
                    {"user_id": session_id},
                    {"$set": {"todos": [value], "updated_at": now}},
                    upsert=True
                )
                logger.debug(f"Created new todos for session_id: {session_id} with value: {value}")
        else:
            raise ValueError("Unsupported field for personalization context saving")
    except Exception as e:
        logger.error(f"Error saving personalization context: {e}")
        # Re-raise the exception to be handled by the caller
        raise