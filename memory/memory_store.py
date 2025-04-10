# memory_store.py
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

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

def get_user_id():
    """Get the user ID from environment variable or use default"""
    return os.environ.get("USER_ID", DEFAULT_USER_ID)

def load_user_memory(user_id=None):
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
        # Try to load from MongoDB
        profile = mongo_db["profile"].find_one({"user_id": user_id})
        todos = list(mongo_db["todos"].find({"user_id": user_id}))
        instructions = mongo_db["instructions"].find_one({"user_id": user_id})
        research_goals = mongo_db["research_goals"].find_one({"user_id": user_id})
        
        # Combine into a single memory object
        memory_data = {
            "profile": profile if profile else {},
            "todos": todos,
            "instructions": instructions.get("content") if instructions else "",
            "research_goals": research_goals.get("content") if research_goals else "",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return memory_data
    else:
        # Load from local file
        with open(MEMORY_PATH, "r") as f:
            all_data = json.load(f)
        return all_data.get(user_id, {})

def save_user_memory(user_id=None, data=None):
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
        # Save to MongoDB collections
        if "profile" in data:
            mongo_db["profile"].update_one(
                {"user_id": user_id},
                {"$set": data["profile"]},
                upsert=True
            )
        
        if "todos" in data:
            # Delete existing todos and insert new ones
            mongo_db["todos"].delete_many({"user_id": user_id})
            if data["todos"]:
                mongo_db["todos"].insert_many(data["todos"])
        
        if "instructions" in data:
            mongo_db["instructions"].update_one(
                {"user_id": user_id},
                {"$set": {"content": data["instructions"]}},
                upsert=True
            )
        
        if "research_goals" in data:
            mongo_db["research_goals"].update_one(
                {"user_id": user_id},
                {"$set": {"content": data["research_goals"]}},
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

def get_user_profile(user_id=None):
    """
    Get the user profile data
    
    Parameters:
        user_id (str, optional): User ID to get profile for. If None, uses the one from environment.
    
    Returns:
        dict: User profile data
    """
    if user_id is None:
        user_id = get_user_id()
        
    memory_data = load_user_memory(user_id)
    return memory_data.get("profile", {})
