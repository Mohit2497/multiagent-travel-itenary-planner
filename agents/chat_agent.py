# Enhanced chat_agent.py - Replace your existing chat_node function

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
    comments = preferences.get('comments', '')
    
    # Build conversation history context
    recent_context = ""
    if chat_history and len(chat_history) > 0:
        recent_context = "\n\nRecent conversation:\n"
        for chat in chat_history[-2:]:  # Last 2 exchanges for context
            recent_context += f"User: {chat['question']}\nYou: {chat['response'][:150]}...\n"
    
    # Extract specific details from itinerary for context
    itinerary_context = ""
    if itinerary:
        itinerary_context = f"\n\nCurrent itinerary highlights:\n{itinerary[:800]}..."
    
    # Create a comprehensive, conversational prompt
    prompt = f"""
    You are a friendly, knowledgeable AI travel assistant helping someone with their {holiday_type} to {destination}. 
    You're like a helpful local friend who knows all the insider secrets.
    
    PERSONALITY:
    - Conversational and warm (talk like a knowledgeable friend, not a robot)
    - Enthusiastic about travel discoveries
    - Give SPECIFIC recommendations with actual names, locations, and practical details
    - Reference their actual trip plans when relevant
    - Keep responses focused and helpful (2-4 sentences usually)
    - Use natural language, occasional emojis, but don't overdo it
    
    TRAVELER'S TRIP DETAILS:
    - Going to: {destination}
    - When: {month}
    - Duration: {duration} days  
    - Group size: {num_people} people
    - Budget level: {budget_type}
    - Trip style: {holiday_type}
    - Special notes: {comments}
    {itinerary_context}
    {recent_context}
    
    CURRENT QUESTION: "{user_question}"
    
    RESPONSE RULES:
    1. Be conversational and specific - avoid generic travel advice
    2. Reference their actual trip details when relevant (dates, group size, budget, etc.)
    3. Give concrete recommendations with names, locations, prices when possible
    4. Connect answers to their existing itinerary if relevant
    5. Keep it helpful but concise (usually 2-4 sentences)
    6. If you don't have specific info, be honest but still helpful
    7. Ask a follow-up question if it would be useful
    
    EXAMPLES OF GOOD RESPONSES:
    ❌ Generic: "There are many great restaurants in the area."
    ✅ Specific: "For authentic pasta near the Colosseum, try Flavio al Velavevodetto - it's about 15 minutes from your Day 2 plans and locals love it. Expect around €15-20 per person for your budget level."
    
    ❌ Generic: "Pack according to the weather."
    ✅ Specific: "Since you're going in {month}, definitely pack layers - mornings can be chilly but afternoons warm up. A light rain jacket would be smart for your outdoor activities on Day 3."
    
    Respond naturally as if you're chatting with a friend who's excited about their upcoming trip!
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
        
        # Ensure response isn't too long for chat interface
        if len(response) > 500:
            # Try to cut at a sentence boundary
            sentences = response.split('. ')
            truncated = '. '.join(sentences[:3])
            if not truncated.endswith('.'):
                truncated += '.'
            response = truncated + " (Want me to elaborate on anything specific?)"
        
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
        error_responses = [
            f"Oops! I'm having a small hiccup. But I'm still excited to help with your {destination} trip! Try asking again? 😊",
            f"Hmm, something went wonky on my end. But I'm here and ready to chat about your {destination} adventure! Give it another shot?",
            f"Technical blip on my side! But I'm pumped to help make your {destination} trip amazing. Try your question again?"
        ]
        
        error_response = random.choice(error_responses)
        
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