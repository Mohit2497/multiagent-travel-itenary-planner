from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from llm_helper import get_llm
import json 

def generate_itinerary(state):
    llm = get_llm()
    prompt = f"""
    Using the following preferences, create a detailed itinerary:
    {json.dumps(state['preferences'], indent=2)}

    Include sections for each day, dining options, and downtime.
    """
    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        return {"itinerary": result.strip()}
    except Exception as e:
        return {"itinerary": "", "warning": str(e)}