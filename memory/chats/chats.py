"""
Module: memory/chats/chats.py

This module provides helper functions for loading, saving, and clearing chat history.
MongoDB is accessed via the helper defined in memory/mongodb/mongo_helper.py.
"""

from datetime import datetime
from memory.mongodb.mongo_helper import CHATS_COLLECTION

def load_chat_history(session_id: str) -> dict:
    """
    Load the stored chat history for a given session from MongoDB.
    
    Parameters:
        session_id (str): Unique identifier for a chat session.
    
    Returns:
        dict: The saved chat state with keys: 'session_memory', 'turns', 'components'.
              If no document is found, returns an initial empty state.
    """
    doc = CHATS_COLLECTION.find_one({"session_id": session_id})
    if doc:
        return doc
    return {"session_memory": {}, "turns": [], "components": {}}

def save_chat_history(session_id: str, session_memory: dict, turns: list, components: dict = None) -> None:
    """
    Save or update the chat history for a given session into MongoDB.
    
    Parameters:
        session_id (str): Unique identifier for a chat session.
        session_memory (dict): The state from the pipeline's memory core.
        turns (list): List of conversation turns (dictionaries with "user" and "bot" keys).
        components (dict, optional): Additional contextual components.
    """
    if components is None:
        components = {}
    
    data = {
        "session_id": session_id,
        "session_memory": session_memory,
        "turns": turns,
        "components": components,
        "updated_at": datetime.utcnow().isoformat()
    }
    # Upsert the record—update if exists, or insert a new document.
    CHATS_COLLECTION.update_one({"session_id": session_id}, {"$set": data}, upsert=True)
    print(f"Chat history saved for session '{session_id}'.")

def clear_chat_history(session_id: str) -> None:
    """
    Delete the chat history for a given session from MongoDB.
    
    Parameters:
        session_id (str): Unique identifier for the chat session.
    """
    CHATS_COLLECTION.delete_one({"session_id": session_id})
    print(f"Chat history cleared for session '{session_id}'.")