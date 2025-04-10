from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

class AdaptiveResponseEngine:
    def __init__(self, mode="therapist", temperature=0.7):
        self.mode = mode
        # Create an LLM instance
        self.llm = ChatOpenAI(model="gpt-4o", temperature=temperature)

    def decide(self, analysis, memory_state, conversation_history):
        try:
            if self.mode == "therapist":
                return self._therapist_response(analysis, memory_state, conversation_history)
            elif self.mode == "security":
                return self._security_response(analysis, conversation_history)
            else:
                raise ValueError(f"Unknown mode: {self.mode}")
        except Exception as e:
            logger.error(f"Error in response generation: {e}")
            # Return a fallback response
            return {"response": "I'm having trouble processing your request right now. Could you please rephrase or try again later?", "mode": self.mode}

    def _therapist_response(self, analysis, memory_state, conversation_history):
        # Extract the user's text from the analysis
        user_text = analysis.get("text", "")
        if not user_text:
            logger.warning("No user text found in analysis")
            return {"response": "I didn't catch that. Could you please repeat?", "mode": "therapist"}
        
        # Construct a dynamic prompt that includes analysis, memory, and conversation context.
        prompt = (
            "You are a compassionate therapist. "
            "Below is the analysis of the recent interaction:\n"
            f"Emotion: {analysis.get('emotion', 'unknown')}\n"
            f"Intent: {analysis.get('intent', 'unknown')}\n"
            f"Topic: {analysis.get('topic', 'unknown')}\n"
            f"Tone: {analysis.get('tone', 'unknown')}\n\n"
            "The following is relevant information from the long-term memory:\n"
            f"{memory_state}\n\n"
        )
        
        # Only include conversation history if it's not empty
        if conversation_history:
            prompt += (
                "And here is the conversation history:\n"
                f"{self._format_conversation(conversation_history)}\n\n"
            )
        
        prompt += (
            "Generate a helpful, empathetic, and context-aware response to the most recent user input. "
            "Make sure to directly address any questions the user has asked. "
            "If the user has shared personal information, acknowledge it and respond appropriately."
        )

        # Call the LLM using a system prompt and the user conversation
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user_text)
        ]
        
        try:
            result = self.llm.invoke(messages)
            return {"response": result.content, "mode": "therapist"}
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return {"response": "I'm having trouble generating a response. Could you please try again?", "mode": "therapist"}

    def _security_response(self, analysis, conversation_history):
        # Extract the user's text from the analysis
        user_text = analysis.get("text", "")
        if not user_text:
            logger.warning("No user text found in analysis")
            return {"response": "I didn't catch that. Could you please repeat?", "mode": "security"}
            
        # Similar dynamic prompt for a security check
        prompt = (
            "You are a security monitor for a conversation. "
            "Please analyze the latest user message in the following conversation. \n"
        )
        
        # Only include conversation history if it's not empty
        if conversation_history:
            prompt += f"Conversation history: {self._format_conversation(conversation_history)}\n\n"
        
        prompt += "Return a response that either warns, blocks, or allows the message based on its risk level."
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user_text)
        ]
        
        try:
            result = self.llm.invoke(messages)
            return {"response": result.content, "mode": "security"}
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return {"response": "I'm having trouble analyzing your message. Please try again.", "mode": "security"}

    def _format_conversation(self, conversation_history):
        # Format the conversation history into a string.
        # Expecting conversation_history to be a list of dicts like {"user": "Hi", "bot": "Hello"}
        formatted = ""
        for turn in conversation_history:
            formatted += f"You: {turn.get('user', '')}\nBot: {turn.get('bot', '')}\n"
        return formatted