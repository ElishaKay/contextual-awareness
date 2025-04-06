# therapist_demo.py
from core.pipeline import TCAPipeline
from memory.langraph_adapter import LangGraphMemoryAdapter

user_id = "demo_user"

print("=== Therapist App ===")
mode = "therapist"

# Load memory
prior_state = LangGraphMemoryAdapter.load_checkpoint(user_id)
pipeline = TCAPipeline(mode)
pipeline.load(prior_state)

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    result = pipeline.process(user_input)
    print("Bot:", result["response"])

    # Save updated memory
    LangGraphMemoryAdapter.save_checkpoint(user_id, pipeline.to_dict())
