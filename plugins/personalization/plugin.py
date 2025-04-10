from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def analyze_personalization_context(user_input):
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)
    prompt = (
        "You are a personalization assistant. Extract personal details, preferences, tasks and goals from user input. "
        "Output a clean JSON without quotes, using only relevant fields:\n"
        "- profile: Personal details, traits, preferences, characteristics, location, job, etc\n"
        "- todos: Tasks, to-dos, things they want/need to do\n"
        "- instructions: How they want things done or how they prefer to be answered\n" 
        "- goals: Short or long-term goals mentioned\n\n"
        "Examples:\n\n"
        "Input: stop being so nice\n"
        "Output: {\n"
        "  instructions: be direct without fluff\n"
        "}\n\n"
        "Input: I live in jerusalem\n" 
        "Output: {\n"
        "  profile: {\n"
        "    location: jerusalem\n"
        "  }\n"
        "}\n\n"
        "Input: i got fired and am trying to build a business\n"
        "Output: {\n"
        "  profile: {\n"
        "    job: got fired recently and trying to build a business\n"
        "  },\n"
        "  goals: [build a business]\n"
        "}\n\n"
        f"User input: {user_input}\n"
    )
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_input)
    ]
    result = llm.invoke(messages)
    try:
        analysis = eval(result.content)
    except Exception:
        analysis = {
            "profile": {},
            "todos": [],
            "instructions": "",
            "goals": ""
        }
    return analysis
