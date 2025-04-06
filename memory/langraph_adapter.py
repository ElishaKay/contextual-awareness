# langgraph_adapter.py
import os
import json

CHECKPOINT_FILE = "memory/langgraph_checkpoints.json"

if not os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({}, f)

class LangGraphMemoryAdapter:
    @staticmethod
    def save_checkpoint(user_id, state_dict):
        with open(CHECKPOINT_FILE, "r") as f:
            all_data = json.load(f)
        all_data[user_id] = state_dict
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(all_data, f, indent=2)

    @staticmethod
    def load_checkpoint(user_id):
        with open(CHECKPOINT_FILE, "r") as f:
            all_data = json.load(f)
        return all_data.get(user_id, {})
