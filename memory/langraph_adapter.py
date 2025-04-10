# langgraph_adapter.py
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
CHECKPOINT_FILE = "memory/langgraph_checkpoints.json"
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
        print("MongoDB connection established for LangGraph checkpoints")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        USE_MONGO = False

# Initialize local file storage if it doesn't exist
if not os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({}, f)

def get_user_id():
    """Get the user ID from environment variable or use default"""
    return os.environ.get("USER_ID", DEFAULT_USER_ID)

class LangGraphMemoryAdapter:
    @staticmethod
    def save_checkpoint(user_id=None, state_dict=None):
        """
        Save checkpoint to either MongoDB or local file storage
        
        Parameters:
            user_id (str, optional): User ID to save checkpoint for. If None, uses the one from environment.
            state_dict (dict, optional): Checkpoint data to save. If None, creates an empty dict.
        """
        if user_id is None:
            user_id = get_user_id()
            
        if state_dict is None:
            state_dict = {}
            
        # Add timestamp
        state_dict["updated_at"] = datetime.utcnow().isoformat()
        
        if USE_MONGO and mongo_db is not None:
            # Save to MongoDB
            mongo_db["langgraph_checkpoints"].update_one(
                {"user_id": user_id},
                {"$set": state_dict},
                upsert=True
            )
            print(f"LangGraph checkpoint saved to MongoDB for user {user_id}")
        else:
            # Save to local file
            with open(CHECKPOINT_FILE, "r") as f:
                all_data = json.load(f)
            all_data[user_id] = state_dict
            with open(CHECKPOINT_FILE, "w") as f:
                json.dump(all_data, f, indent=2)
            print(f"LangGraph checkpoint saved to local file for user {user_id}")

    @staticmethod
    def load_checkpoint(user_id=None):
        """
        Load checkpoint from either MongoDB or local file storage
        
        Parameters:
            user_id (str, optional): User ID to load checkpoint for. If None, uses the one from environment.
            
        Returns:
            dict: Checkpoint data
        """
        if user_id is None:
            user_id = get_user_id()
            
        if USE_MONGO and mongo_db is not None:
            # Load from MongoDB
            checkpoint = mongo_db["langgraph_checkpoints"].find_one({"user_id": user_id})
            if checkpoint:
                # Remove MongoDB _id field
                if "_id" in checkpoint:
                    del checkpoint["_id"]
                return checkpoint
            return {}
        else:
            # Load from local file
            with open(CHECKPOINT_FILE, "r") as f:
                all_data = json.load(f)
            return all_data.get(user_id, {})
