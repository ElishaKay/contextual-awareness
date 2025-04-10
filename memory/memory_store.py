# memory_store.py
import json
import os
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

# File system storage path
MEMORY_PATH = "memory/user_memory.json"

# Ensure the directory exists
os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)

# Initialize the file if it doesn't exist
if not os.path.exists(MEMORY_PATH):
    with open(MEMORY_PATH, "w") as f:
        json.dump({}, f)

def _get_mongo_db():
    """Get MongoDB connection if USE_MONGO is set to true"""
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise EnvironmentError("MONGO_URI not set")
    client = MongoClient(mongo_uri)
    return client["gptr_db"]

def _use_mongo():
    """Check if MongoDB should be used based on environment variable"""
    return os.environ.get("USE_MONGO", "false").lower() == "true"

def load_user_memory(user_id):
    """
    Load user memory from either MongoDB or file system based on environment variables
    """
    if _use_mongo():
        try:
            db = _get_mongo_db()
            user_data = db["users"].find_one({"user_id": user_id})
            if user_data:
                # Convert MongoDB document to dict and remove _id field
                user_dict = dict(user_data)
                if "_id" in user_dict:
                    del user_dict["_id"]
                return user_dict
            return {}
        except Exception as e:
            logger.warning(f"Failed to load from MongoDB: {e}. Falling back to file system.")
            # Fall back to file system if MongoDB fails
            pass
    
    # File system fallback
    with open(MEMORY_PATH, "r") as f:
        all_data = json.load(f)
    return all_data.get(user_id, {})

def save_user_memory(user_id, data):
    """
    Save user memory to either MongoDB or file system based on environment variables
    """
    if _use_mongo():
        try:
            db = _get_mongo_db()
            # Add timestamp for tracking
            data["updated_at"] = datetime.utcnow().isoformat()
            
            # Upsert the document
            db["users"].update_one(
                {"user_id": user_id},
                {"$set": data},
                upsert=True
            )
            logger.debug(f"Saved user memory to MongoDB for user_id: {user_id}")
            return
        except Exception as e:
            logger.warning(f"Failed to save to MongoDB: {e}. Falling back to file system.")
            # Fall back to file system if MongoDB fails
            pass
    
    # File system fallback
    with open(MEMORY_PATH, "r") as f:
        all_data = json.load(f)
    all_data[user_id] = data
    with open(MEMORY_PATH, "w") as f:
        json.dump(all_data, f, indent=2)
    logger.debug(f"Saved user memory to file system for user_id: {user_id}")

def update_user_profile(user_id, profile_info):
    """
    Update user profile information in memory
    """
    user_data = load_user_memory(user_id)
    
    # Initialize profile if it doesn't exist
    if "profile" not in user_data:
        user_data["profile"] = {}
    
    # Update profile with new information
    user_data["profile"].update(profile_info)
    
    # Save updated user data
    save_user_memory(user_id, user_data)
    logger.debug(f"Updated user profile for user_id: {user_id}")
