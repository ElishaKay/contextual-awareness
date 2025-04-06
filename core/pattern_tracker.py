# pattern_tracker.py

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import json
import re

class PatternShiftTracker:
    def __init__(self, temperature=0.7):
        """
        Initializes the PatternShiftTracker with an LLM instance for nuanced analysis.
        
        Parameters:
            temperature (float): Controls the randomness of the LLM output.
        """
        # Create an instance of ChatOpenAI (or any other LLM interface)
        self.llm = ChatOpenAI(model="gpt-4o", temperature=temperature)

    def track(self, turn_history, current_analysis):
        """
        Tracks changes in emotional tone by comparing the previous turn with the current analysis.
        If an emotional drift is detected, uses an LLM to provide a detailed explanation.

        Parameters:
            turn_history (list): List of past conversation turns (dictionaries).
            current_analysis (dict): Analysis of the current user input, expected to include an "emotion" key.

        """
        # No history available? Return early.
        if not turn_history:
            return {"change": "none", "details": "No previous conversation to compare."}

        # Extract emotions from the last turn and the current analysis.
        last_emotion = turn_history[-1]
        current_emotion = current_analysis

        # If both emotions exist and differ, use the LLM for additional insight.
        if last_emotion and current_emotion:
            prompt = (
                "Analyze the change in emotional tone between these two states:\n"
                f" - Previous emotion: {str(last_emotion)!r}\n"
                f" - Current emotion: {str(current_emotion)!r}\n"
                "First, determine if this represents a significant emotional shift or if it's relatively stable.\n"
                "Then provide a brief explanation of your assessment.\n"
                "Format your response as a JSON with two fields: 'change': Either 'emotion_drift' or 'stable', 'details': Your explanation \n"
                "Ensure your response is valid JSON."
            )
            messages = [
                SystemMessage(content="You are an expert in psychological analysis and conversation dynamics."),
                HumanMessage(content=prompt)
            ]

            try:
                # Invoke the language model and extract the response
                llm_response = self.llm.invoke(messages)
                response_content = llm_response.content
                
                # Print the raw response for debugging
                # print(f"Raw LLM response: {response_content}")
                
                # Try to extract JSON from the response if it's not pure JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    # print(f"Extracted JSON: {json_str}")
                    result = json.loads(json_str)
                else:
                    # If no JSON found, create a default response
                    result = {
                        "change": "stable",
                        "details": "Could not parse LLM response as JSON. Defaulting to stable."
                    }
                
                return result
            except Exception as e:
                # Log the error and return stable state
                print(f"Error parsing LLM response: {str(e)}")
                return {
                    "change": "stable", 
                    "details": f"LLM analysis failed: {str(e)}, defaulting to stable"
                }
        else:
            return {"change": "stable", "details": "The emotional state remains stable."}