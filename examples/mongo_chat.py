"""
File: examples/mongo_chat.py

This demo illustrates using MongoDB persistence for chat history and enhanced
personalization logic. Personalization context is both fetched and updated via
the core/personalization_context module.

Before running, set these environment variables (via your shell or .env file):
    USE_MONGO=true
    MONGO_URI=<your MongoDB connection string>
    USER_ID=<a unique user id (can be null)>
    (Optional) SESSION_ID – if not provided, one will be generated.
"""

import os
import uuid

from core.pipeline import TCAPipeline
from memory.chats.chats import load_chat_history, save_chat_history
from memory.vectorstore.vectorstore import load_vector_store

def main():
    # Create (or retrieve) a session_id.
    session_id = os.environ.get("SESSION_ID", str(uuid.uuid4()))
    # USER_ID is not used directly in chat saving now (it may be stored within the personalization DB documents)
    use_mongo = os.environ.get("USE_MONGO", "false").lower() == "true"

    if use_mongo:
        print("Using MongoDB persistence for chat history.")
        chat_state = load_chat_history(session_id)
    else:
        print("Using default in-memory persistence for chat history.")
        chat_state = {"session_memory": {}, "turns": [], "components": {}}

    # Initialize the pipeline (providing the session_id so personalization functions work).
    pipeline = TCAPipeline(mode="therapist", session_id=session_id)
    pipeline.load(chat_state)

    # Optionally load the vector store.
    vector_store = load_vector_store()
    print("MongoDB vector store has been loaded.")

    print("Starting conversation. Type 'exit' to quit.")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            break

        # Process user input via the pipeline.
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
            print("In-memory state updated.")

if __name__ == "__main__":
    main()