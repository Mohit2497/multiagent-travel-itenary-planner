from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama

# Try different DuckDuckGo import methods
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from duckduckgo_search import ddg
        DDGS = ddg
    except ImportError:
        print("Warning: DuckDuckGo search not available, using basic search fallback")
        DDGS = None

def food_culture_recommender(state):
    """Enhanced food and culture recommender with real restaurant data"""
    
    destination = state['preferences'].get('destination', '')
    budget = state['preferences'].get('budget_type', 'mid-range')
    holiday_type = state['preferences'].get('holiday_type', 'any')
    duration = state['preferences'].get('duration', 7)
    
    print(f"🔍 Searching for real restaurants in {destination}...")
    
    # Step 1: Get real restaurant data from DuckDuckGo (with fallback)
    restaurant_context = ""
    
    if DDGS is not None:
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
                            max_results=3
                        ))
                        all_restaurant_results.extend(results)
                    except Exception as e:
                        print(f"Query failed: {query} - {str(e)}")
                        continue
                
                # Process results
                if all_restaurant_results:
                    restaurant_context = "REAL RESTAURANT DATA FROM WEB SEARCH:\n"
                    for i, result in enumerate(all_restaurant_results[:12]):
                        title = result.get('title', 'Unknown')
                        snippet = result.get('body', '')[:200]
                        url = result.get('href', '')
                        
                        restaurant_context += f"\n{i+1}. {title}\n"
                        restaurant_context += f"   Details: {snippet}\n"
                        restaurant_context += f"   Source: {url}\n"
                    
                    print(f"✅ Found {len(all_restaurant_results)} restaurant results")
                else:
                    restaurant_context = "No restaurant data found from web search."
                    print("❌ No restaurant results found")
                    
        except Exception as e:
            restaurant_context = f"Restaurant search unavailable: {str(e)}"
            print(f"❌ Restaurant search error: {str(e)}")
    else:
        restaurant_context = "Web search currently unavailable. Providing general recommendations."
        print("⚠️ DuckDuckGo search not available")
    
    # Step 2: Use AI to curate the results (same as before)
    from llm_helper import get_llm
    llm = get_llm()
    
    prompt = f"""
    You are a travel expert providing dining and cultural advice for {destination}.
    
    {restaurant_context}
    
    Based on the restaurant search results above (if available), create comprehensive dining and cultural recommendations for a {duration}-day {holiday_type} trip with a {budget} budget.
    
    Structure your response with these sections:
    
    ## 🍽️ **Dining Recommendations**
    
    ### **Fine Dining** (if budget allows)
    [List restaurants from search results that appear to be upscale, or provide general fine dining guidance]
    
    ### **Local Favorites & Authentic Cuisine**
    [List restaurants from search results that seem to offer local/traditional food, or provide general local food guidance]
    
    ### **Casual Dining & Popular Spots**
    [List restaurants from search results that appear casual/popular, or provide general recommendations]
    
    ### **Cafes & Quick Bites**
    [List cafes and quick dining options from search results, or provide general cafe recommendations]
    
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
    - If restaurant search results are available, prioritize those recommendations
    - If no search results, provide well-known general recommendations for {destination}
    - Include practical information like typical meal times, reservation needs, etc.
    - Be helpful and informative regardless of search availability
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