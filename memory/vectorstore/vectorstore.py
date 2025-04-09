"""
Module: memory/vectorstore/vectorstore.py

This module provides a helper to instantiate a MongoDB-backed vector store using the
Atlas integration. It uses the connection defined in memory/mongodb/mongo_helper.py.
"""

from memory.mongodb.mongo_helper import MONGO_URI, db
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch

def load_vector_store() -> MongoDBAtlasVectorSearch:
    """
    Instantiate and return a MongoDBAtlasVectorSearch instance.
    
    Returns:
        MongoDBAtlasVectorSearch: A vector store instance backed by MongoDB.
    """
    embeddings = OpenAIEmbeddings(disallowed_special=())
    # The full collection string needs to include database and collection.
    full_collection = "gptr_db.vector_store"
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        MONGO_URI,
        full_collection,
        embeddings,
        index_name="default"
    )
    return vector_store