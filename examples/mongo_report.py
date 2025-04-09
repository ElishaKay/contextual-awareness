from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from pymongo import MongoClient

# Import your schema definitions
from memory.mongodb.schema import Report, Log, Chat

# Import the necessary classes from your vector store and GPTR packages
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from gpt_researcher import GPTResearcher

################################################################################
# MongoDB Setup
################################################################################

# Read MongoDB URI from environment variable
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable must be set")

# Create the underlying client and get a database reference.
client = MongoClient(MONGO_URI)
# We are using the "gptr_db" for this example (adjust as needed)
db = client["gptr_db"]

# Collections for different types of data (vector store, reports, logs, chats)
VECTOR_COLLECTION = db["vector_store"]
REPORTS_COLLECTION = db["reports"]
LOGS_COLLECTION = db["logs"]
CHATS_COLLECTION = db["chats"]

################################################################################
# 1. Create the MongoDB Vector Store
################################################################################

def create_mongo_vector_store():
    """Instantiates a MongoDB vector store using the Atlas integration."""
    embeddings = OpenAIEmbeddings(disallowed_special=())
    # Note: The collection is specified with the full name "database.collection"
    full_collection = "gptr_db.vector_store"
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        MONGO_URI,
        full_collection,
        embeddings,
        index_name="default"
    )
    return vector_store

################################################################################
# 2. Create a Custom Logs Handler
################################################################################

class CustomLogsHandler:
    """A custom logs handler class to process and store logs as JSON into MongoDB."""
    def __init__(self, logs_collection):
        self.logs_collection = logs_collection
        self.logs = []

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Handle a JSON log entry by storing it locally and in MongoDB."""
        # Append to an in-memory list (if you need to keep runtime logs)
        self.logs.append(data)
        print(f"My custom Log: {data}")
        # Also add a created_at timestamp and insert into the MongoDB logs collection
        data["created_at"] = datetime.utcnow().isoformat()
        self.logs_collection.insert_one(data)

################################################################################
# 3. Helper Functions to Save Report & Chat Data
################################################################################

def save_report_to_db(report_content: str):
    """Save a final report to the reports collection in MongoDB."""
    report = Report(
        report_id=str(datetime.utcnow().timestamp()),
        content=report_content,
        created_at=datetime.utcnow().isoformat()
    )
    REPORTS_COLLECTION.insert_one(report.dict())
    print("Report saved to MongoDB.")

def save_chat_to_db(conversation: list):
    """Save a chat transcript to the chats collection in MongoDB."""
    chat = Chat(
        chat_id=str(datetime.utcnow().timestamp()),
        conversation=conversation,
        created_at=datetime.utcnow().isoformat()
    )
    CHATS_COLLECTION.insert_one(chat.dict())
    print("Chat saved to MongoDB.")

################################################################################
# 4. Main Flow Function
################################################################################

async def run_flow():
    # Create a MongoDB vector store instance
    vector_store = create_mongo_vector_store()

    # Define your research query
    query = "who is elishakay of the gpt-researcher github repo?"

    # Initialize your custom logs handler to stream and save log messages
    custom_logs_handler = CustomLogsHandler(LOGS_COLLECTION)

    # Instantiate GPTResearcher with the following key parameters:
    # • query, report_type, and report_source ("web" to add scraped data to your vector store)
    # • vector_store (the MongoDB backed vector store)
    # • websocket set to your custom logs handler (for streaming logs)
    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        report_source="web",
        vector_store=vector_store,
        websocket=custom_logs_handler
    )

    # Conduct research—this will embed and store the scraped web data into the MongoDB vector store.
    await researcher.conduct_research()

    # Generate the research report from the previously stored context.
    report = await researcher.write_report()
    print("Final Report:", report)

    # Save the report into the MongoDB reports collection.
    save_report_to_db(report)

    # (Optional) Capture the conversation for the current run and save it into a chats collection.
    # In practice this may come from your state or logs.
    conversation = [
        f"User: {query}",
        f"Researcher: {report}"
    ]
    save_chat_to_db(conversation)

    # (Optional) Query the vector store for similar contexts and print the outcomes.
    related_contexts = await vector_store.asimilarity_search("GPT-4", k=5)
    print("Related vector store contexts:")
    for idx, doc in enumerate(related_contexts):
        print(f"Result {idx+1}: {doc.page_content}")

################################################################################
# 5. Run the Flow
################################################################################

if __name__ == "__main__":
    asyncio.run(run_flow())