from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class AdaptiveResponseEngine:
    def __init__(self, mode="therapist", temperature=0.7):
        self.mode = mode
        # Create an LLM instance
        self.llm = ChatOpenAI(model="gpt-4o", temperature=temperature)

    def decide(self, analysis, memory_state, conversation_history):
        if self.mode == "therapist":
            return self._therapist_response(analysis, memory_state, conversation_history)
        elif self.mode == "security":
            return self._security_response(analysis, conversation_history)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _therapist_response(self, analysis, memory_state, conversation_history):
        # Construct a dynamic prompt that includes analysis, memory, and conversation context.
        prompt = (
            "You are a compassionate therapist. "
            "Below is the analysis of the recent interaction:\n"
            f"Emotion: {analysis.get('emotion')}\n"
            f"Intent: {analysis.get('intent')}\n\n"
            "The following is relevant information from the long-term memory:\n"
            f"{memory_state}\n\n"
            "And here is the conversation history:\n"
            f"{self._format_conversation(conversation_history)}\n\n"
            "Generate a helpful, empathetic, and context-aware response to the most recent user input."
        )

        # Call the LLM using a system prompt and the user conversation (you could refine further by separating roles)
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=conversation_history[-1]["user"])  # most recent user message
        ]
        result = self.llm.invoke(messages)
        return {"response": result.content, "mode": "therapist"}

    def _security_response(self, analysis, conversation_history):
        # Similar dynamic prompt for a security check
        prompt = (
            "You are a security monitor for a conversation. "
            "Please analyze the latest user message in the following conversation. \n"
            f"Conversation history: {self._format_conversation(conversation_history)}\n\n"
            "Return a response that either warns, blocks, or allows the message based on its risk level."
        )
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=conversation_history[-1]["user"]) 
        ]
        result = self.llm.invoke(messages)
        # For simplicity, assume the system returns an object with a key "response"
        return {"response": result.content, "mode": "security"}

    def _format_conversation(self, conversation_history):
        # Format the conversation history into a string.
        # Expecting conversation_history to be a list of dicts like {"user": "Hi", "bot": "Hello"}
        formatted = ""
        for turn in conversation_history:
            formatted += f"You: {turn.get('user')}\nBot: {turn.get('bot', '')}\n"
        return formatted