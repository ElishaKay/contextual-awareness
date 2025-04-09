"""
Module: core/personalization_context.py

This module handles all operations related to fetching and saving a user’s
personalization context. In our schema, we manage the following collections:
    - "profile"        (stores a simple profile/info document keyed by user_id)
    - "todos"          (stores one todo per record keyed by user_id)
    - "instructions"   (stores a document with a "content" field, keyed by user_id)
    - "research_goals" (stores a document with a "goals" field, keyed by user_id)
    
Each document includes a created_at field (and updated_at for updates).
"""

import os
from datetime import datetime
from pymongo import MongoClient

def _get_mongo_db():
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise EnvironmentError("MONGO_URI not set")
    client = MongoClient(mongo_uri)
    return client["gptr_db"]

def fetch_personalization_context(session_id: str) -> dict:
    """
    Retrieves personalization context from MongoDB for a given session_id.
    Looks up the profile, todos, instructions, and research_goals.
    """
    db = _get_mongo_db()
    profile = db["profile"].find_one({"user_id": session_id})
    todos = list(db["todos"].find({"user_id": session_id}))
    instructions_doc = db["instructions"].find_one({"user_id": session_id})
    research_goals_doc = db["research_goals"].find_one({"user_id": session_id})
    
    context = {
        "profile": profile if profile else {},
        "todos": todos,
        "instructions": instructions_doc.get("content") if instructions_doc else "",
        "research_goals": research_goals_doc.get("goals") if research_goals_doc else ""
    }
    return context

def save_personalization_context(session_id: str, field: str, value: str):
    """
    Saves (or updates) a personalization field for the given session_id.
    
    Allowed fields:
      - "profile":      a string containing user's profile info.
      - "instructions": a string to be saved in the instructions collection.
      - "research_goals": a string to be saved in the research_goals collection.
      - "todos":        a todo item (each todo is a separate record).
    
    For "profile", "instructions", and "research_goals", the document is upserted.
    For "todos", a new record is inserted.
    Each record includes a created_at (and updated_at on update) field.
    """
    db = _get_mongo_db()
    now = datetime.utcnow().isoformat()

    if field == "profile":
        existing = db["profile"].find_one({"user_id": session_id})
        if existing:
            # Append new info if not already present.
            current_info = existing.get("info", "")
            if value not in current_info:
                updated_info = (current_info + " " + value).strip()
                db["profile"].update_one(
                    {"user_id": session_id},
                    {"$set": {"info": updated_info, "updated_at": now}}
                )
        else:
            db["profile"].insert_one({
                "user_id": session_id,
                "info": value,
                "created_at": now
            })
    elif field in ["instructions", "research_goals"]:
        col = "instructions" if field == "instructions" else "research_goals"
        field_key = "content" if field == "instructions" else "goals"
        existing = db[col].find_one({"user_id": session_id})
        if existing:
            db[col].update_one(
                {"user_id": session_id},
                {"$set": {field_key: value, "updated_at": now}}
            )
        else:
            db[col].insert_one({
                "user_id": session_id,
                field_key: value,
                "created_at": now
            })
    elif field == "todos":
        db["todos"].insert_one({
            "user_id": session_id,
            "todo": value,
            "created_at": now
        })
    else:
        raise ValueError("Unsupported field for personalization context saving")