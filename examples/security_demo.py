# security_demo.py
from dotenv import load_dotenv
load_dotenv()

from core.pipeline import TCAPipeline
from memory.langraph_adapter import LangGraphMemoryAdapter

user_id = "demo_user"

print("=== Security App ===")
mode = "security"

# Load memory from a previous checkpoint (if any)
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