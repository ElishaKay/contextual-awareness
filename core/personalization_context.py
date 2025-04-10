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
        profile_doc = db["profile"].find_one({"user_id": session_id})
        # Return profile_doc as a dict if found; otherwise, an empty dict.
        profile = profile_doc if profile_doc and isinstance(profile_doc, dict) else {}
        
        todos = list(db["todos"].find({"user_id": session_id}))
        instructions_doc = db["instructions"].find_one({"user_id": session_id})
        research_goals_doc = db["research_goals"].find_one({"user_id": session_id})
        
        context = {
            "profile": profile,
            "todos": todos,
            "instructions": instructions_doc.get("content") if instructions_doc else "",
            "research_goals": research_goals_doc.get("goals") if research_goals_doc else ""
        }
        logger.debug(f"Fetched personalization context for session_id: {session_id}")
        return context
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

    For the first three, the document is upserted. For "todos", a new document is inserted.
    """
    try:
        db = _get_mongo_db()
        now = datetime.utcnow().isoformat()

        if field == "profile":
            existing = db["profile"].find_one({"user_id": session_id})
            if existing:
                # Append new information if it's not already present.
                current_info = existing.get("info", "")
                if value not in current_info:
                    updated_info = (current_info + " " + value).strip()
                    db["profile"].update_one(
                        {"user_id": session_id},
                        {"$set": {"info": updated_info, "updated_at": now}}
                    )
                    logger.debug(f"Updated profile for session_id: {session_id} with value: {value}")
            else:
                db["profile"].insert_one({
                    "user_id": session_id,
                    "info": value,
                    "created_at": now,
                    "updated_at": now
                })
                logger.debug(f"Created new profile for session_id: {session_id} with value: {value}")
        elif field in ["instructions", "research_goals"]:
            col = "instructions" if field == "instructions" else "research_goals"
            field_key = "content" if field == "instructions" else "goals"
            existing = db[col].find_one({"user_id": session_id})
            if existing:
                db[col].update_one(
                    {"user_id": session_id},
                    {"$set": {field_key: value, "updated_at": now}}
                )
                logger.debug(f"Updated {field} for session_id: {session_id} with value: {value}")
            else:
                db[col].insert_one({
                    "user_id": session_id,
                    field_key: value,
                    "created_at": now,
                    "updated_at": now
                })
                logger.debug(f"Created new {field} for session_id: {session_id} with value: {value}")
        elif field == "todos":
            db["todos"].insert_one({
                "user_id": session_id,
                "todo": value,
                "created_at": now,
                "updated_at": now
            })
            logger.debug(f"Added new todo for session_id: {session_id} with value: {value}")
        else:
            raise ValueError("Unsupported field for personalization context saving")
    except Exception as e:
        logger.error(f"Error saving personalization context: {e}")
        # Re-raise the exception to be handled by the caller
        raise