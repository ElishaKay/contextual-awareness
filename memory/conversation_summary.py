"""
Module: memory/conversation_summary.py

This module provides functionality to generate and manage conversation summaries
that can be stored in the user profile for future reference.
"""

from typing import List, Dict
import logging
import json
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from core.memory_core import TemporalMemoryCore

logger = logging.getLogger(__name__)

def generate_conversation_summary(conversation_history: List[Dict[str, str]], user_id: str) -> str:
    """
    Generate a summary of the conversation history.
    
    Args:
        conversation_history: List of conversation messages
        user_id: The user's ID
        
    Returns:
        str: A summary of the conversation
    """
    try:
        # Get the last 20 messages for summarization
        recent_messages = conversation_history[-20:]
        
        # Create a prompt for the summary
        messages_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])
        
        prompt = f"""Please provide a concise summary of the following conversation, focusing on:
1. Key topics discussed
2. Important information shared
3. Any decisions or action items
4. User preferences or interests mentioned

Conversation:
{messages_text}

Summary:"""
        
        # TODO: Replace with actual LLM call when available
        # For now, return a placeholder summary
        summary = f"Conversation summary for user {user_id} - {len(recent_messages)} messages reviewed"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating conversation summary: {str(e)}")
        return ""

def save_conversation_summary(user_id: str, summary: str) -> bool:
    """
    Save the conversation summary to the user's profile.
    
    Args:
        user_id: The user's ID
        summary: The conversation summary to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        memory_core = TemporalMemoryCore(user_id)
        user = memory_core.load_user_context()
        
        if user:
            user.conversation_summary = summary
            user.last_summary_update = datetime.utcnow().isoformat()
            memory_core.update_user_context(conversation_summary=summary, last_summary_update=datetime.utcnow().isoformat())
            logger.info(f"Saved conversation summary for user {user_id}")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error saving conversation summary: {str(e)}")
        return False

def get_conversation_summary(user_id: str) -> str:
    """
    Retrieve the conversation summary for a user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        str: The conversation summary, or empty string if not found
    """
    try:
        memory_core = TemporalMemoryCore(user_id)
        user = memory_core.load_user_context()
        
        if user and user.conversation_summary:
            return user.conversation_summary
            
        return ""
        
    except Exception as e:
        logger.error(f"Error retrieving conversation summary: {str(e)}")
        return "" 