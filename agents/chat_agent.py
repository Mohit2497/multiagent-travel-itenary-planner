from langchain_core.messages import HumanMessage
from llm_helper import get_llm
import json
import random

def chat_node(state):
    """Enhanced conversational chat agent with personality and context awareness"""
    
    # Get LLM
    llm = get_llm()
    
    # Extract context information
    preferences = state.get('preferences', {})
    itinerary = state.get('itinerary', '')
    user_question = state.get('user_question', '')
    chat_history = state.get('chat_history', [])
    
    # Get trip context
    destination = preferences.get('destination', 'your destination')
    duration = preferences.get('duration', 'several days')
    budget_type = preferences.get('budget_type', 'mid-range')
    holiday_type = preferences.get('holiday_type', 'trip')
    num_people = preferences.get('num_people', '1')
    month = preferences.get('month', '')
    
    # Conversation starters and personality elements
    friendly_greetings = [
        "Great question!",
        "I love helping with that!",
        "Ooh, interesting!",
        "That's a fantastic question!",
        "I'm excited to help with this!",
        "Perfect timing for this question!"
    ]
    
    # Build conversation history context
    recent_context = ""
    if chat_history and len(chat_history) > 0:
        recent_context = "\n\nRecent conversation context:\n"
        for chat in chat_history[-3:]:  # Last 3 exchanges
            recent_context += f"User asked: {chat['question']}\n"
            recent_context += f"I responded: {chat['response'][:100]}...\n"
    
    # Create a comprehensive, conversational prompt
    prompt = f"""
    You are an enthusiastic, knowledgeable, and friendly AI travel assistant helping with a {holiday_type} trip to {destination}. 
    
    PERSONALITY TRAITS:
    - Conversational and warm (like talking to a travel-savvy friend)
    - Enthusiastic about travel and discoveries
    - Specific and practical (avoid generic advice)
    - Use the traveler's name/trip details to personalize responses
    - Share insider tips and local knowledge
    - Ask follow-up questions when appropriate
    - Use emojis sparingly but effectively
    
    TRIP CONTEXT:
    - Destination: {destination}
    - Duration: {duration} days
    - Travel Month: {month}
    - Group: {num_people} people
    - Budget: {budget_type}
    - Style: {holiday_type}
    - Current Itinerary: {itinerary[:500]}... (truncated)
    
    {recent_context}
    
    CURRENT QUESTION: "{user_question}"
    
    RESPONSE GUIDELINES:
    1. Start with a friendly, engaging opener (not generic like "That's a great question")
    2. Reference their specific trip details (destination, dates, group size, etc.)
    3. Give SPECIFIC recommendations with names, addresses, or exact details when possible
    4. Include practical tips (timing, costs, booking advice, insider secrets)
    5. Connect to their itinerary when relevant
    6. End with a follow-up question or offer for more help
    7. Keep it conversational (100-200 words max unless they ask for detailed info)
    8. Avoid generic travel advice - be specific to their destination and situation
    
    EXAMPLES OF SPECIFIC VS GENERIC:
    ❌ Generic: "Try local restaurants and popular attractions"
    ✅ Specific: "For authentic {destination} cuisine, hit up [specific restaurant name] on [street name] - they're known for [specific dish]. It's about a 10-minute walk from your Day 2 museum visit!"
    
    ❌ Generic: "Check the weather and pack accordingly"
    ✅ Specific: "Since you're visiting {destination} in {month}, expect [specific weather]. Pack layers because mornings can be [temperature] but afternoons warm up to [temperature]."
    
    Respond naturally and conversationally, as if you're a knowledgeable local friend helping them plan the perfect trip!
    """
    
    try:
        # Generate response
        result = llm.invoke([HumanMessage(content=prompt)]).content
        
        # Clean up response (remove any JSON formatting if present)
        response = result.strip()
        if response.startswith('{') and response.endswith('}'):
            try:
                parsed = json.loads(response)
                response = parsed.get("response", response)
            except:
                pass
        
        # Add to chat history
        chat_entry = {
            "question": user_question, 
            "response": response
        }
        updated_chat_history = chat_history + [chat_entry]
        
        print(f"✅ Chat response generated ({len(response)} chars)")
        
        return {
            "chat_response": response, 
            "chat_history": updated_chat_history
        }
        
    except Exception as e:
        # Friendly error message
        error_response = f"Oops! I'm having a small technical hiccup right now. But I'm still here to help with your {destination} trip! Could you try asking your question again? 😊"
        
        chat_entry = {
            "question": user_question, 
            "response": error_response
        }
        updated_chat_history = chat_history + [chat_entry]
        
        print(f"❌ Chat error: {str(e)}")
        
        return {
            "chat_response": error_response, 
            "chat_history": updated_chat_history,
            "warning": str(e)
        }