# memory_store.py
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, Any, Optional, List

# Load environment variables
load_dotenv()

# Configuration
MEMORY_PATH = "memory/user_memory.json"
USE_MONGO = os.environ.get("USE_MONGO", "false").lower() == "true"
MONGO_URI = os.environ.get("MONGO_URI", "")
DEFAULT_USER_ID = os.environ.get("USER_ID", "default-user")

# Initialize MongoDB connection if enabled
mongo_client = None
mongo_db = None
if USE_MONGO and MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_db = mongo_client["gptr_db"]
        print("MongoDB connection established")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        USE_MONGO = False

# Initialize local file storage if it doesn't exist
if not os.path.exists(MEMORY_PATH):
    with open(MEMORY_PATH, "w") as f:
        json.dump({}, f)

def get_user_id() -> str:
    """Get the user ID from environment variable or use default"""
    return os.environ.get("USER_ID", DEFAULT_USER_ID)

def get_or_create_user(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get or create a user document in the users collection
    
    Parameters:
        user_id (str, optional): User ID to get/create. If None, uses the one from environment.
    
    Returns:
        dict: User document
    """
    if user_id is None:
        user_id = get_user_id()
        
    if USE_MONGO and mongo_db is not None:
        user = mongo_db["users"].find_one({"user_id": user_id})
        if not user:
            # Create new user document
            user = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "profile": {},
                "preferences": {},
                "conversation_history": []
            }
            mongo_db["users"].insert_one(user)
            print(f"Created new user document for {user_id}")
        return user
    else:
        return {"user_id": user_id, "profile": {}, "preferences": {}, "conversation_history": []}

def update_user_activity(user_id: Optional[str] = None) -> None:
    """
    Update the last_active timestamp for a user
    
    Parameters:
        user_id (str, optional): User ID to update. If None, uses the one from environment.
    """
    if user_id is None:
        user_id = get_user_id()
        
    if USE_MONGO and mongo_db is not None:
        mongo_db["users"].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.utcnow()}}
        )

def load_user_memory(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load user memory from either MongoDB or local file storage
    
    Parameters:
        user_id (str, optional): User ID to load memory for. If None, uses the one from environment.
    
    Returns:
        dict: User memory data
    """
    if user_id is None:
        user_id = get_user_id()
        
    if USE_MONGO and mongo_db is not None:
        # Get or create user document
        user = get_or_create_user(user_id)
                
        # Combine into a single memory object
        memory_data = {
            "profile": user.get("profile", {}),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Update last active timestamp
        update_user_activity(user_id)
        
        return memory_data
    else:
        # Load from local file
        with open(MEMORY_PATH, "r") as f:
            all_data = json.load(f)
        return all_data.get(user_id, {})

def save_user_memory(user_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Save user memory to either MongoDB or local file storage
    
    Parameters:
        user_id (str, optional): User ID to save memory for. If None, uses the one from environment.
        data (dict, optional): Memory data to save. If None, creates an empty dict.
    """
    if user_id is None:
        user_id = get_user_id()
    
    if data is None:
        data = {}
    
    if USE_MONGO and mongo_db is not None:
        # Update user document
        user_update = {
            "profile": data.get("profile", {}),
            "preferences": data.get("preferences", {}),
            "last_active": datetime.utcnow()
        }
        mongo_db["users"].update_one(
            {"user_id": user_id},
            {"$set": user_update},
            upsert=True
        )
        
        print(f"User memory saved to MongoDB for user {user_id}")
    else:
        # Save to local file
        with open(MEMORY_PATH, "r") as f:
            all_data = json.load(f)
        all_data[user_id] = data
        with open(MEMORY_PATH, "w") as f:
            json.dump(all_data, f, indent=2)
        print(f"User memory saved to local file for user {user_id}")

def get_user_profile(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the user profile data
    
    Parameters:
        user_id (str, optional): User ID to get profile for. If None, uses the one from environment.
    
    Returns:
        dict: User profile data
    """
    if user_id is None:
        user_id = get_user_id()
        
    if USE_MONGO and mongo_db is not None:
        user = get_or_create_user(user_id)
        return user.get("profile", {})
    else:
        memory_data = load_user_memory(user_id)
        return memory_data.get("profile", {})

def update_user_profile(user_id: Optional[str] = None, profile_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the user profile data
    
    Parameters:
        user_id (str, optional): User ID to update profile for. If None, uses the one from environment.
        profile_data (dict, optional): Profile data to update. If None, creates an empty dict.
    """
    if user_id is None:
        user_id = get_user_id()
    
    if profile_data is None:
        profile_data = {}
        
    if USE_MONGO and mongo_db is not None:
        try:
            # Get existing user document or create new one
            user = get_or_create_user(user_id)
            
            # Update the profile data
            current_profile = user.get("profile", {})
            current_profile.update(profile_data)
            
            # Update the user document with new profile data
            mongo_db["users"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "profile": current_profile,
                        "last_active": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Also update the profile in the chats collection for consistency
            mongo_db["chats"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_profile": current_profile,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                },
                upsert=True
            )
            
            print(f"Updated profile for user {user_id} in all collections")
        except Exception as e:
            print(f"Error updating profile in MongoDB: {e}")
            raise
    else:
        # Save to local file
        memory_data = load_user_memory(user_id)
        memory_data["profile"] = profile_data
        save_user_memory(user_id, memory_data)
