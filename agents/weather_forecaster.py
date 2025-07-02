from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from llm_helper import get_llm

def weather_forecaster(state):
    llm = get_llm()
    prompt = f"""
    Based on the destination and month, provide a detailed weather forecast including temperature, precipitation, and advice for travelers:
    Destination: {state['preferences'].get('destination', '')}
    Month: {state['preferences'].get('month', '')}
    """
    try:
        result = llm.invoke([HumanMessage(content=prompt)]).content
        return {"weather_forecast": result.strip()}
    except Exception as e:
        return {"weather_forecast": "", "warning": str(e)}