"""
File: examples/mongo_chat.py

This demo illustrates using MongoDB persistence for chat history and
a MongoDB-backed vector store within the contextual awareness flow.
Before running, set the following environment variables (e.g., via your shell or .env file):
    USE_MONGO=true
    MONGO_URI=<your MongoDB connection string>
    USER_ID=<a unique user id>
"""

import os
import asyncio

from core.pipeline import TCAPipeline
from memory.chats.chats import load_chat_history, save_chat_history
from memory.vectorstore.vectorstore import load_vector_store

def main():
    # Use environment variables to get the session identifier and whether to use Mongo.
    session_id = os.environ.get("USER_ID", "default-user")
    use_mongo = os.environ.get("USE_MONGO", "false").lower() == "true"

    if use_mongo:
        print("Using MongoDB persistence for chat history.")
        chat_state = load_chat_history(session_id)
    else:
        # Fallback: initialize with an empty state.
        print("Using default in-memory persistence for chat history.")
        chat_state = {"session_memory": {}, "turns": [], "components": {}}

    # Initialize the pipeline (this is your core conversation processor).
    pipeline = TCAPipeline(mode="therapist")
    pipeline.load(chat_state)

    # Optionally load the vector store.
    vector_store = load_vector_store()
    print("MongoDB vector store has been loaded.")

    print("Starting conversation. Type 'exit' to quit.")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            break

        response = pipeline.process(user_input)
        print("Bot:", response.get("response"))

        # Persist the updated pipeline state.
        state = pipeline.to_dict()
        if use_mongo:
            save_chat_history(session_id,
                              state.get("session_memory", {}),
                              state.get("turns", []),
                              state.get("components", {}))
        else:
            # In a real fallback solution you might write the state to a file.
            print("In-memory state updated.")

if __name__ == "__main__":
    main()