from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from llm_helper import get_llm
from duckduckgo_search import DDGS

def food_culture_recommender(state):
    """Enhanced food and culture recommender with real restaurant data"""
    
    destination = state['preferences'].get('destination', '')
    budget = state['preferences'].get('budget_type', 'mid-range')
    holiday_type = state['preferences'].get('holiday_type', 'any')
    duration = state['preferences'].get('duration', 7)
    
    print(f"🔍 Searching for real restaurants in {destination}...")  # Debug info
    
    # Step 1: Get real restaurant data from DuckDuckGo
    restaurant_context = ""
    try:
        with DDGS() as ddgs:
            # Multiple targeted searches for better results
            search_queries = [
                f"best restaurants {destination} {budget} popular 2024",
                f"top rated restaurants {destination} TripAdvisor Yelp",
                f"local restaurants {destination} must try authentic",
                f"popular cafes {destination} local favorites",
                f"{destination} restaurant guide where to eat"
            ]
            
            all_restaurant_results = []
            
            for query in search_queries:
                try:
                    results = list(ddgs.text(
                        keywords=query,
                        region='wt-wt',
                        safesearch='moderate',
                        max_results=3  # 3 results per query
                    ))
                    all_restaurant_results.extend(results)
                except Exception as e:
                    print(f"Query failed: {query} - {str(e)}")
                    continue
            
            # Process and format the restaurant results
            if all_restaurant_results:
                restaurant_context = "REAL RESTAURANT DATA FROM WEB SEARCH:\n"
                for i, result in enumerate(all_restaurant_results[:12]):  # Top 12 results
                    title = result.get('title', 'Unknown')
                    snippet = result.get('body', '')[:200]  # First 200 chars
                    url = result.get('href', '')
                    
                    restaurant_context += f"\n{i+1}. {title}\n"
                    restaurant_context += f"   Details: {snippet}\n"
                    restaurant_context += f"   Source: {url}\n"
                
                print(f"✅ Found {len(all_restaurant_results)} restaurant results")
            else:
                restaurant_context = "No current restaurant data found from web search."
                print("❌ No restaurant results found")
                
    except Exception as e:
        restaurant_context = f"Restaurant search failed: {str(e)}"
        print(f"❌ Restaurant search error: {str(e)}")
    
    # Step 2: Use AI to curate the results with cultural information
    llm = get_llm()
    
    prompt = f"""
    You are a travel expert providing dining and cultural advice for {destination}.
    
    {restaurant_context}
    
    Based on the REAL restaurant search results above, create comprehensive dining and cultural recommendations for a {duration}-day {holiday_type} trip with a {budget} budget.
    
    Structure your response with these sections:
    
    ## 🍽️ **Dining Recommendations**
    
    ### **Fine Dining** (if budget allows)
    [List restaurants from search results that appear to be upscale]
    
    ### **Local Favorites & Authentic Cuisine**
    [List restaurants from search results that seem to offer local/traditional food]
    
    ### **Casual Dining & Popular Spots**
    [List restaurants from search results that appear casual/popular]
    
    ### **Cafes & Quick Bites**
    [List cafes and quick dining options from search results]
    
    ## 🎭 **Culture & Etiquette**
    
    ### **Local Dishes to Try**
    [Traditional/signature dishes of the destination]
    
    ### **Dining Customs**
    [Local dining etiquette, tipping customs, meal times]
    
    ### **Cultural Tips**
    [Important cultural norms, dress codes, behavior expectations]
    
    ### **Food Shopping & Markets**
    [Local markets, food shopping tips, specialties to buy]
    
    **IMPORTANT INSTRUCTIONS:**
    - ONLY recommend specific restaurants that were mentioned in the search results above
    - Do NOT invent restaurant names - only use what was found in the web search
    - If no restaurants were found in search results, focus more on general dining advice and cultural tips
    - Be specific about why each restaurant is recommended based on the search result information
    - Include practical information like typical meal times, reservation needs, etc.
    """
    
    try:
        print("🤖 Generating curated recommendations...")
        result = llm.invoke([HumanMessage(content=prompt)]).content
        print("✅ Recommendations generated successfully")
        return {"food_culture_info": result.strip()}
    except Exception as e:
        print(f"❌ AI generation error: {str(e)}")
        return {
            "food_culture_info": f"Unable to generate dining recommendations at this time. Error: {str(e)}", 
            "warning": str(e)
        }