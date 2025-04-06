# therapist_demo.py

from core.meaning_engine import ContextualMeaningEngine
from core.pattern_tracker import PatternShiftTracker
from core.memory_core import TemporalMemoryCore
from core.response_engine import AdaptiveResponseEngine
from memory.langgraph_adapter import load_user_memory, save_user_memory

# Initialize modules
meaning_engine = ContextualMeaningEngine()
pattern_tracker = PatternShiftTracker()
memory_core = TemporalMemoryCore()
response_engine = AdaptiveResponseEngine()

# Simulated input (could come from a user-facing chat UI)
user_id = "user_001"
user_input = "I just feel like I’m not good enough anymore. It’s hard to get out of bed."
session_history = []

# Load past long-term memory from LangGraph
prior_memory = load_user_memory(user_id)
memory_core.load(prior_memory)

# Step 1: Analyze intent, emotion, and topic
analysis = meaning_engine.analyze(user_input)

# Step 2: Detect shifts and changes
patterns = pattern_tracker.track(session_history, analysis)

# Step 3: Update short-term memory
session_state = memory_core.update(analysis, patterns)

# Step 4: Generate a contextual response
response = response_engine.decide(analysis, session_state)

# Step 5: Display output
print("User:", user_input)
print("Agent:", response["response"])

# Step 6: Persist memory after session
save_user_memory(user_id, memory_core.to_dict())
