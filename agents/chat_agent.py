# FIXED chat_agent.py - Replace your entire chat_agent.py file with this

from langchain_core.messages import HumanMessage
import json
import random

def chat_node(state):
    """Working chat agent that provides actual travel responses"""
    
    print("🔄 Chat agent called...")  # Debug log
    
    try:
        # Import LLM inside the function to avoid import issues
        from llm_helper import get_llm
        llm = get_llm()
        print("✅ LLM loaded successfully")  # Debug log
        
        # Extract context information safely
        preferences = state.get('preferences', {})
        itinerary = state.get('itinerary', '')
        user_question = state.get('user_question', '')
        chat_history = state.get('chat_history', [])
        
        # Get trip context with defaults
        destination = preferences.get('destination', 'the destination')
        duration = preferences.get('duration', 'several days')
        budget_type = preferences.get('budget_type', 'mid-range')
        holiday_type = preferences.get('holiday_type', 'trip')
        num_people = preferences.get('num_people', '1')
        month = preferences.get('month', '')
        comments = preferences.get('comments', '')
        
        print(f"📍 Processing question about {destination}: {user_question}")  # Debug log
        
        # Build conversation context
        context_info = f"""
TRIP DETAILS:
- Destination: {destination}
- Month: {month}
- Duration: {duration} days
- Group size: {num_people} people
- Budget: {budget_type}
- Trip type: {holiday_type}
- Special notes: {comments}
"""
        
        # Add recent chat context
        if chat_history:
            context_info += "\nRecent conversation:\n"
            for chat in chat_history[-2:]:
                context_info += f"User: {chat['question'][:100]}...\n"
                context_info += f"Assistant: {chat['response'][:100]}...\n"
        
        # Create a focused prompt
        prompt = f"""You are a friendly AI travel assistant helping with a trip to {destination}.

{context_info}

CURRENT QUESTION: "{user_question}"

Provide a helpful, specific response about {destination}. Be conversational and practical. Give actual recommendations with names, locations, or specific advice when possible. Keep your response to 2-4 sentences.

Examples of good responses:
- For restaurants: "For authentic Kashmiri food, try Ahdoos Restaurant in Lal Chowk - they're famous for their Rogan Josh and Kahwa tea. It's about ₹800-1200 for two people and locals love it."
- For saving money: "Stay in Srinagar's old city guesthouses (₹1500-2500/night vs ₹8000+ for hotels), eat at local dhabas, and use shared taxis instead of private cars."
- For activities: "Visit Shalimar Gardens early morning (7 AM) to avoid crowds and get the best photos. Entry is just ₹25 per person."

Respond naturally and helpfully!"""

        print("📝 Sending prompt to LLM...")  # Debug log
        
        # Generate response
        result = llm.invoke([HumanMessage(content=prompt)])
        response = result.content.strip()
        
        print(f"✅ LLM response received: {len(response)} chars")  # Debug log
        
        # Clean up response
        if response.startswith('{') and response.endswith('}'):
            try:
                parsed = json.loads(response)
                response = parsed.get("response", response)
            except:
                pass
        
        # Ensure reasonable length
        if len(response) > 500:
            sentences = response.split('. ')
            if len(sentences) > 3:
                response = '. '.join(sentences[:3]) + '.'
        
        # Ensure proper ending
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        # Create chat entry
        chat_entry = {
            "question": user_question,
            "response": response
        }
        
        # Update chat history
        updated_chat_history = chat_history + [chat_entry]
        
        print(f"✅ Chat response generated successfully")  # Debug log
        
        return {
            "chat_response": response,
            "chat_history": updated_chat_history
        }
        
    except Exception as e:
        print(f"❌ Error in chat_node: {str(e)}")  # Debug log
        
        # Check specific error types
        error_type = type(e).__name__
        print(f"❌ Error type: {error_type}")  # Debug log
        
        if "llm_helper" in str(e) or "get_llm" in str(e):
            error_response = f"I'm having trouble connecting to my brain right now! 🧠 Could you try asking about your {destination} trip again in a moment?"
        elif "invoke" in str(e):
            error_response = f"My thinking circuits got tangled! 🤖 Let me try to help with your {destination} question again - just ask once more!"
        else:
            error_response = f"Oops! Something went wonky on my end. But I'm still excited to help with your {destination} adventure! Try asking again? 😊"
        
        # Create error chat entry
        chat_entry = {
            "question": user_question,
            "response": error_response
        }
        
        # Update chat history with error
        updated_chat_history = chat_history + [chat_entry]
        
        return {
            "chat_response": error_response,
            "chat_history": updated_chat_history,
            "error": f"{error_type}: {str(e)}"
        }

# Alternative simple chat function if the above doesn't work
def simple_chat_response(state):
    """Fallback chat function with hardcoded responses"""
    
    user_question = state.get('user_question', '').lower()
    destination = state.get('preferences', {}).get('destination', 'your destination')
    chat_history = state.get('chat_history', [])
    
    # Simple keyword-based responses
    if 'restaurant' in user_question or 'food' in user_question or 'eat' in user_question:
        response = f"For authentic local food in {destination}, I'd recommend trying the traditional dishes at local family-run restaurants. Look for places where locals eat - they usually have the best authentic flavors and reasonable prices!"
    
    elif 'money' in user_question or 'save' in user_question or 'budget' in user_question:
        response = f"Great question! To save money in {destination}: stay in local guesthouses instead of hotels, eat at local eateries, use public transport, and look for free walking tours. Local markets are also great for affordable meals and souvenirs!"
    
    elif 'hidden' in user_question or 'gem' in user_question or 'secret' in user_question:
        response = f"For hidden gems in {destination}, I'd suggest exploring local neighborhoods away from main tourist areas. Ask locals for their favorite spots - they often know amazing places that aren't in guidebooks!"
    
    elif 'time' in user_question or 'when' in user_question or 'timing' in user_question:
        response = f"For the best experience in {destination}, visit popular attractions early morning or late afternoon to avoid crowds. Weekdays are generally less busy than weekends!"
    
    elif 'transport' in user_question or 'taxi' in user_question or 'travel' in user_question:
        response = f"For getting around {destination}, local transport is usually the most economical option. Shared taxis or buses work well for longer distances, while walking or cycling is great for exploring city centers!"
    
    else:
        response = f"That's a great question about {destination}! While I'd love to give you specific details, I recommend checking with locals or recent travelers for the most up-to-date information. Is there something specific about your trip I can help you plan?"
    
    # Create chat entry
    chat_entry = {
        "question": state.get('user_question', ''),
        "response": response
    }
    
    # Update chat history
    updated_chat_history = chat_history + [chat_entry]
    
    return {
        "chat_response": response,
        "chat_history": updated_chat_history
    }