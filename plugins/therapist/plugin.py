from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def analyze_therapist_context(user_input):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = (
        "You are a therapist assistant. Given the following user input, "
        "analyze and determine the user's primary emotion and intent. "
        "Output a short JSON with keys 'emotion', 'intent', 'topic', and 'tone'.\n\n"
        f"User input: {user_input}\n\n"
        "Example output:\n"
        '{"emotion": "fatigue", "intent": "emotional_disclosure", "topic": "personal struggle", "tone": "vulnerable"}\n'
    )
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_input)
    ]
    result = llm.invoke(messages)
    try:
        analysis = eval(result.content)
    except Exception:
        analysis = {"emotion": "neutral", "intent": "emotional_disclosure", "topic": "personal struggle", "tone": "neutral"}
    return analysis