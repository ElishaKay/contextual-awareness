from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def analyze_security_context(user_input):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = (
        "You are a security compliance analyzer. Given the following user input, "
        "analyze and determine potential security risks and concerns. "
        "Output a short JSON with keys 'intent', 'emotion', 'topic', 'tone', and 'risk_level'.\n\n"
        f"User input: {user_input}\n\n"
        "Example output:\n"
        '{"intent": "general_query", "emotion": "neutral", "topic": "security compliance", "tone": "technical", "risk_level": "low"}\n'
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
            "intent": "general_query",
            "emotion": "neutral", 
            "topic": "security compliance",
            "tone": "technical",
            "risk_level": "low"
        }
    return analysis