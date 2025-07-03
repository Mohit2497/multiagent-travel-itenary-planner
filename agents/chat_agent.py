# GENERALIZED CHAT AGENT FOR ALL DESTINATIONS
# Replace your entire chat_agent.py file with this

import json
import random

def chat_node(state):
    """Universal chat agent that works for any destination worldwide"""
    
    # Extract information safely
    preferences = state.get('preferences', {})
    user_question = state.get('user_question', '')
    chat_history = state.get('chat_history', [])
    
    destination = preferences.get('destination', 'your destination')
    budget_type = preferences.get('budget_type', 'mid-range')
    num_people = preferences.get('num_people', '1')
    month = preferences.get('month', '')
    holiday_type = preferences.get('holiday_type', 'trip')
    
    print(f"🎯 Processing question: '{user_question}' for destination: '{destination}'")
    
    try:
        # Try LLM first with improved error handling
        from llm_helper import get_llm
        llm = get_llm()
        
        # Create focused prompt for any destination
        prompt = f"""You are an experienced travel guide with deep knowledge of {destination}. Answer this traveler's question with specific, practical advice.

TRAVELER'S QUESTION: "{user_question}"

TRIP CONTEXT:
- Destination: {destination}
- Travel month: {month}
- Group size: {num_people} people
- Budget level: {budget_type}
- Trip type: {holiday_type}

RESPONSE REQUIREMENTS:
- Be specific to {destination} (mention actual places, districts, or landmarks when possible)
- Include practical details (costs, timing, locations, booking tips)
- Keep response conversational and helpful (150-250 words max)
- Give actionable advice the traveler can actually use
- If you mention prices, use appropriate currency for the destination
- Focus on authentic, local experiences rather than tourist traps

Answer as a knowledgeable local friend would:"""

        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        response = result.content.strip()
        
        # Validate LLM response quality
        if (len(response) > 40 and 
            "sorry" not in response.lower()[:50] and 
            "don't know" not in response.lower() and
            "can't help" not in response.lower()):
            
            print("✅ LLM response successful")
            final_response = clean_response(response)
        else:
            raise Exception("LLM response quality insufficient")
            
    except Exception as e:
        print(f"⚠️ LLM failed ({str(e)}), using intelligent universal fallback")
        final_response = get_universal_response(user_question, destination, preferences)
    
    # Ensure proper response format
    if not final_response.endswith(('.', '!', '?')):
        final_response += '.'
    
    # Create chat entry
    chat_entry = {
        "question": user_question,
        "response": final_response
    }
    
    # Update chat history
    updated_chat_history = chat_history + [chat_entry]
    
    print(f"✅ Response generated: {final_response[:100]}...")
    
    return {
        "chat_response": final_response,
        "chat_history": updated_chat_history
    }

def clean_response(response):
    """Clean and format the LLM response"""
    # Remove JSON formatting if present
    if response.startswith('{') and response.endswith('}'):
        try:
            parsed = json.loads(response)
            response = parsed.get("response", response)
        except:
            pass
    
    # Remove common AI prefixes
    prefixes_to_remove = [
        "As an AI", "I'm an AI", "Based on my knowledge",
        "According to my information", "I should mention",
        "It's worth noting that", "I must say"
    ]
    
    for prefix in prefixes_to_remove:
        if response.startswith(prefix):
            # Find the first sentence and start from there
            sentences = response.split('. ')
            if len(sentences) > 1:
                response = '. '.join(sentences[1:])
            break
    
    return response.strip()

def get_universal_response(question, destination, preferences):
    """Generate intelligent responses that work for any destination"""
    
    question_lower = question.lower()
    budget = preferences.get('budget_type', 'mid-range')
    people = preferences.get('num_people', '1')
    month = preferences.get('month', '')
    holiday_type = preferences.get('holiday_type', 'trip')
    
    # Determine question category and generate appropriate response
    if is_food_question(question_lower):
        return get_food_response(destination, budget, people)
    elif is_budget_question(question_lower):
        return get_budget_response(destination, budget, people)
    elif is_hidden_gems_question(question_lower):
        return get_hidden_gems_response(destination, holiday_type)
    elif is_timing_question(question_lower):
        return get_timing_response(destination, month)
    elif is_transportation_question(question_lower):
        return get_transportation_response(destination, budget)
    elif is_accommodation_question(question_lower):
        return get_accommodation_response(destination, budget, people)
    elif is_safety_question(question_lower):
        return get_safety_response(destination)
    elif is_culture_question(question_lower):
        return get_culture_response(destination)
    elif is_weather_question(question_lower):
        return get_weather_response(destination, month)
    elif is_activity_question(question_lower):
        return get_activity_response(destination, holiday_type, budget)
    else:
        return get_general_response(destination, question, preferences)

# Question category detection functions
def is_food_question(question):
    food_keywords = ['restaurant', 'food', 'eat', 'dining', 'cuisine', 'meal', 'lunch', 'dinner', 'breakfast', 'cafe', 'bar', 'drink']
    return any(keyword in question for keyword in food_keywords)

def is_budget_question(question):
    budget_keywords = ['money', 'save', 'budget', 'cheap', 'affordable', 'cost', 'price', 'expensive', 'free']
    return any(keyword in question for keyword in budget_keywords)

def is_hidden_gems_question(question):
    gems_keywords = ['hidden', 'gem', 'secret', 'off beaten', 'local', 'authentic', 'undiscovered', 'lesser known']
    return any(keyword in question for keyword in gems_keywords)

def is_timing_question(question):
    timing_keywords = ['time', 'when', 'timing', 'hour', 'best time', 'avoid crowds', 'busy', 'quiet']
    return any(keyword in question for keyword in timing_keywords)

def is_transportation_question(question):
    transport_keywords = ['transport', 'taxi', 'bus', 'train', 'metro', 'getting around', 'travel', 'uber', 'car', 'bike']
    return any(keyword in question for keyword in transport_keywords)

def is_accommodation_question(question):
    accommodation_keywords = ['hotel', 'stay', 'accommodation', 'hostel', 'guesthouse', 'airbnb', 'where to stay']
    return any(keyword in question for keyword in accommodation_keywords)

def is_safety_question(question):
    safety_keywords = ['safe', 'safety', 'dangerous', 'crime', 'scam', 'avoid', 'precaution']
    return any(keyword in question for keyword in safety_keywords)

def is_culture_question(question):
    culture_keywords = ['culture', 'custom', 'tradition', 'etiquette', 'behavior', 'respect', 'dress code']
    return any(keyword in question for keyword in culture_keywords)

def is_weather_question(question):
    weather_keywords = ['weather', 'rain', 'temperature', 'climate', 'season', 'pack', 'clothes']
    return any(keyword in question for keyword in weather_keywords)

def is_activity_question(question):
    activity_keywords = ['activity', 'attraction', 'sightseeing', 'museum', 'park', 'beach', 'shopping', 'nightlife', 'entertainment']
    return any(keyword in question for keyword in activity_keywords)

# Response generation functions
def get_food_response(destination, budget, people):
    responses = [
        f"🍽️ For authentic food in {destination}: Look for restaurants packed with locals - that's always the best sign! Ask your hotel staff where they personally eat, visit local markets for fresh ingredients and street food, and don't be afraid to try regional specialties. For {budget} budget dining, family-run establishments usually offer the best value and most authentic flavors.",
        
        f"🍽️ Food tips for {destination}: The best meals are often found away from main tourist areas. Ask locals about their favorite family restaurants, check out where office workers eat lunch (good food + reasonable prices), and visit local food markets in the morning for fresh options. Street food from busy stalls is usually safe and delicious!",
        
        f"🍽️ Dining in {destination}: For great local cuisine, look for places where you hear the local language being spoken - that's where residents eat! Try traditional dishes specific to the region, ask servers for their recommendations, and don't miss local markets for authentic snacks and ingredients you can't find elsewhere."
    ]
    return random.choice(responses)

def get_budget_response(destination, budget, people):
    responses = [
        f"💰 Money-saving tips for {destination}: Stay in local neighborhoods rather than tourist centers (often 30-50% cheaper), eat where locals eat instead of tourist restaurants, use public transportation, look for free walking tours and city events. Many museums and attractions offer discounted days or hours!",
        
        f"💰 Budget advice for {destination}: Choose accommodations with kitchen facilities to save on meals, shop at local markets instead of convenience stores, use city tourism cards for attraction discounts, and join free activities like hiking, beach visits, or exploring local neighborhoods. Group bookings often get discounts too!",
        
        f"💰 Save money in {destination}: Book accommodations slightly outside the city center, eat your main meal at lunch (often cheaper than dinner), use public transport day passes, visit free attractions like parks and markets, and ask locals about happy hour specials and student discounts."
    ]
    return random.choice(responses)

def get_hidden_gems_response(destination, holiday_type):
    responses = [
        f"💎 Hidden gems in {destination}: Explore residential neighborhoods where locals live and work, visit during weekday mornings when tourist sites are quieter, ask shop owners and café staff about their favorite local spots. The best discoveries often happen when you wander off the main tourist paths!",
        
        f"💎 Local secrets in {destination}: Check out where young professionals hang out after work, visit local markets early in the morning, explore university areas for authentic culture, and ask taxi drivers about interesting places tourists don't usually visit. Often the most memorable experiences aren't in guidebooks!",
        
        f"💎 Authentic {destination} experiences: Look for community events and festivals, visit local libraries or community centers to see daily life, explore side streets near famous attractions, and connect with locals through language exchanges or hobby groups. The real magic happens away from tourist crowds!"
    ]
    return random.choice(responses)

def get_timing_response(destination, month):
    responses = [
        f"⏰ Best timing for {destination}: Visit popular attractions early morning (first hour of opening) or late afternoon to avoid crowds. Weekdays are generally quieter than weekends. For restaurants, lunch hours (12-2 PM) can be busy, while early dinner (5-6 PM) is often quieter with better service.",
        
        f"⏰ Perfect timing in {destination}: Early morning visits offer cooler temperatures and fewer crowds at outdoor attractions. Late afternoon is ideal for photography with golden hour lighting. Avoid peak tourist hours (10 AM-2 PM) at major sites. Evening is perfect for exploring local neighborhoods and experiencing nightlife.",
        
        f"⏰ Timing tips for {destination}: Start your day early to beat crowds and heat (if applicable). Mid-morning to early afternoon is ideal for indoor attractions. Late afternoon and evening are perfect for strolling local areas and meeting locals. Check local customs for lunch breaks and siesta times."
    ]
    return random.choice(responses)

def get_transportation_response(destination, budget):
    responses = [
        f"🚗 Getting around {destination}: Public transportation is usually the most economical and efficient option. Download local transport apps, consider day/week passes for savings, and don't hesitate to ask locals for directions. Walking is often the best way to discover hidden spots in city centers!",
        
        f"🚗 Transportation in {destination}: Local buses and trains are budget-friendly and give you a real taste of daily life. Shared rides or ride-sharing apps are convenient for longer distances. For short distances, walking or renting a bike lets you explore at your own pace and discover interesting detours.",
        
        f"🚗 Moving around {destination}: Mix different transport methods - public transport for longer distances, walking for exploration, and occasional taxis for convenience or safety at night. Many cities offer tourist transport cards that include multiple modes of transport plus attraction discounts."
    ]
    return random.choice(responses)

def get_accommodation_response(destination, budget, people):
    responses = [
        f"🏨 Accommodation in {destination}: For {budget} stays with {people} people, look for local guesthouses or family-run hotels in residential areas - they're often cheaper and more authentic than chain hotels. Check recent reviews, ensure good location for public transport, and don't hesitate to negotiate for longer stays.",
        
        f"🏨 Where to stay in {destination}: Consider neighborhoods slightly outside the main tourist center for better value and local atmosphere. Look for places with kitchen facilities to save on meal costs, good transport connections, and positive recent reviews from travelers with similar interests to yours.",
        
        f"🏨 Lodging tips for {destination}: Book accommodations with good transport links to save time and money. Local guesthouses often provide insider tips from hosts. Consider the balance between location, comfort, and cost - sometimes spending a bit more on location saves money on transport."
    ]
    return random.choice(responses)

def get_safety_response(destination):
    responses = [
        f"🛡️ Safety in {destination}: Use common sense precautions - keep valuables secure, stay aware of your surroundings, and trust your instincts. Ask locals or your accommodation about areas to avoid, especially at night. Keep copies of important documents and have emergency contacts readily available.",
        
        f"🛡️ Staying safe in {destination}: Blend in with local dress and behavior, avoid displaying expensive items, and stay in well-lit, populated areas at night. Learn basic local emergency phrases and keep your accommodation's contact information handy. Most locals are helpful if you need assistance.",
        
        f"🛡️ Safety tips for {destination}: Research common local scams beforehand, keep emergency money separate from your main funds, and inform someone of your daily plans. Use licensed taxis or reputable ride-sharing apps, especially at night. Most destinations are quite safe with basic precautions."
    ]
    return random.choice(responses)

def get_culture_response(destination):
    responses = [
        f"🌍 Cultural tips for {destination}: Learn basic greetings and 'please/thank you' in the local language - locals appreciate the effort! Observe and respect local customs, dress codes at religious sites, and dining etiquette. Ask permission before photographing people, and be open to different ways of doing things.",
        
        f"🌍 Respecting culture in {destination}: Research local customs before arriving, dress appropriately for religious or formal sites, and be patient with different concepts of time and service. Showing genuine interest in local culture often leads to wonderful interactions and authentic experiences.",
        
        f"🌍 Cultural awareness in {destination}: Be respectful of local traditions, even if they're different from your own. Learn about tipping customs, appropriate behavior in religious spaces, and social norms. Most cultural misunderstandings are forgiven when you show respect and willingness to learn."
    ]
    return random.choice(responses)

def get_weather_response(destination, month):
    month_text = f" in {month}" if month else ""
    responses = [
        f"🌤️ Weather in {destination}{month_text}: Check recent weather patterns before your trip and pack accordingly. Layers are usually your best bet for changing temperatures throughout the day. Don't forget rain protection and comfortable walking shoes. Local weather apps often provide more accurate forecasts than international ones.",
        
        f"🌤️ Climate considerations for {destination}{month_text}: Weather can be unpredictable, so pack for various conditions. Lightweight, quick-dry clothing is versatile for most climates. Check if your travel dates coincide with rainy seasons or extreme weather patterns, and plan indoor alternatives for outdoor activities.",
        
        f"🌤️ Preparing for {destination}'s weather{month_text}: Pack versatile clothing that can be layered, and always include a light rain jacket. Comfortable, broken-in walking shoes are essential. Check local weather patterns and ask locals about typical conditions - they know best what to expect day-to-day."
    ]
    return random.choice(responses)

def get_activity_response(destination, holiday_type, budget):
    responses = [
        f"🎯 Activities in {destination}: Mix popular attractions with local experiences for the best of both worlds. Many cities offer free walking tours, public parks, markets, and cultural events. Check local event calendars and don't be afraid to ask locals about current happenings during your visit.",
        
        f"🎯 Things to do in {destination}: Balance must-see attractions with spontaneous discoveries. Free or low-cost activities like hiking, beach visits, market exploration, and people-watching often provide the most authentic experiences. Join local events or festivals if your timing aligns.",
        
        f"🎯 Exploring {destination}: Create a loose itinerary but leave room for spontaneity. Some of the best travel memories come from unexpected discoveries. Mix tourist attractions with local neighborhoods, and don't pack every moment - sometimes the best activity is simply observing daily life with a coffee in hand."
    ]
    return random.choice(responses)

def get_general_response(destination, question, preferences):
    """Fallback response for questions that don't fit specific categories"""
    responses = [
        f"✨ Great question about {destination}! For the most current and detailed information, I'd recommend connecting with locals when you arrive - they often have the best insider knowledge. Also check recent travel forums and local tourism websites for up-to-date tips specific to your interests.",
        
        f"✨ Interesting question about {destination}! Every destination has its unique character and hidden surprises. I'd suggest being open to spontaneous discoveries, asking locals for their personal recommendations, and balancing planned activities with flexibility to explore what captures your interest.",
        
        f"✨ That's a thoughtful question about {destination}! The best travel experiences often come from a mix of research and local insights. Don't hesitate to ask residents, fellow travelers, or local tourism offices for current recommendations tailored to your specific interests and travel style."
    ]
    return random.choice(responses)