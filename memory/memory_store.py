# memory_store.py
import json
import os

MEMORY_PATH = "memory/user_memory.json"

if not os.path.exists(MEMORY_PATH):
    with open(MEMORY_PATH, "w") as f:
        json.dump({}, f)

def load_user_memory(user_id):
    with open(MEMORY_PATH, "r") as f:
        all_data = json.load(f)
    return all_data.get(user_id, {})

def save_user_memory(user_id, data):
    with open(MEMORY_PATH, "r") as f:
        all_data = json.load(f)
    all_data[user_id] = data
    with open(MEMORY_PATH, "w") as f:
        json.dump(all_data, f, indent=2)
