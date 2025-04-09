# memory/mongodb/mongo_helper.py
from dotenv import load_dotenv
load_dotenv()  # load environment variables from .env, if available

import os
from pymongo import MongoClient

# Get the MongoDB URI from the environment.
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable must be set")

# Create a global MongoClient and initialize the database.
client = MongoClient(MONGO_URI)
db = client["gptr_db"]

# Collections for different types of data.
VECTOR_COLLECTION = db["vector_store"]
REPORTS_COLLECTION = db["reports"]
LOGS_COLLECTION = db["logs"]
CHATS_COLLECTION = db["chats"]