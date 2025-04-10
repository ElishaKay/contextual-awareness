# meaning_engine.py
import logging
from plugins.therapist.plugin import analyze_therapist_context
from plugins.security.plugin import analyze_security_context
from memory.memory_store import update_user_profile
from core.personalization_context import save_personalization_context

logger = logging.getLogger(__name__)

class ContextualMeaningEngine:
    def __init__(self, mode="therapist", user_id="default-user"):
        self.mode = mode
        self.user_id = user_id

    def analyze(self, user_input):
        # Get the base analysis from the appropriate plugin
        if self.mode == "therapist":
            analysis = analyze_therapist_context(user_input)
        elif self.mode == "security":
            analysis = analyze_security_context(user_input)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        # Add the original text to the analysis for reference
        analysis["text"] = user_input
        
        # Extract personal information if available
        self._extract_personal_info(user_input, analysis)
        
        return analysis
    
    def _extract_personal_info(self, user_input, analysis):
        """
        Extract personal information from user input and update the user profile.
        This method looks for patterns that indicate the user is sharing personal information.
        """
        # Check if the input contains personal information indicators
        personal_info_indicators = [
            "i am", "i'm", "my name is", "i live", "my age", "i work", 
            "my job", "my family", "my wife", "my husband", "my children",
            "my kids", "my parents", "my friend", "my friends", "my hobby",
            "my hobbies", "my favorite", "i like", "i love", "i hate",
            "i feel", "i think", "i believe", "my experience", "my life"
        ]
        
        # Check if any personal info indicators are in the input
        lower_input = user_input.lower()
        has_personal_info = any(indicator in lower_input for indicator in personal_info_indicators)
        
        if has_personal_info:
            # Extract the personal information
            # This is a simple approach - in a real system, you might use NLP to extract entities
            personal_info = {
                "last_shared_info": user_input,
                "topic": analysis.get("topic", "personal information"),
                "timestamp": analysis.get("timestamp", "")
            }
            
            # Update the user profile with the extracted information
            update_user_profile(self.user_id, personal_info)
            
            # Also save to personalization context
            # Extract the key information from the user input
            # For example, if user says "I like pants", we want to save "I like pants"
            # If user says "My name is John", we want to save "My name is John"
            save_personalization_context(self.user_id, "profile", user_input)
            
            # Add a flag to the analysis indicating personal info was detected
            analysis["contains_personal_info"] = True
            logger.debug(f"Personal information detected and profile updated for user: {self.user_id}")
        else:
            analysis["contains_personal_info"] = False
