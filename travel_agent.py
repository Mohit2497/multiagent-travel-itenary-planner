import streamlit as st
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
import os
from agents import generate_itinerary, recommend_activities, fetch_useful_links, weather_forecaster, packing_list_generator, food_culture_recommender,chat_agent
from llm_helper import get_llm, get_llm_info
from utils_export import export_to_pdf

# Load environment variables
load_dotenv()

# ========== UI IMPROVEMENTS START - LINE 15 ==========
# Enhanced page configuration with better styling and responsive layout
st.set_page_config(
    page_title="AI Travel Planner", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="expanded"  # NEW: Sidebar expanded by default
)

# NEW: Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .metric-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    .trip-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# NEW: Enhanced header with gradient styling
st.markdown("""
<div class="main-header">
    <h1>🌍 AI Travel Planner ✈️</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Create your perfect itinerary with AI-powered recommendations</p>
</div>
""", unsafe_allow_html=True)
# ========== UI IMPROVEMENTS CONTINUE ==========

try:
    llm = get_llm()
    llm_info = get_llm_info()
    st.sidebar.info(f"🤖 {llm_info['provider']} ({llm_info['model']}) - {llm_info['mode']} Mode")
except Exception as e:
    st.error(f"Error initializing Ollama model: {e}")
    st.stop()

# Initialize the Google Serper API wrapper
try:
    search = GoogleSerperAPIWrapper(api_key=os.getenv("SERPER_API_KEY"))
except Exception as e:
    st.error(f"Error initializing Google Serper API: {e}")
    st.stop()

# Define the state graph for the travel agent
class GraphState(TypedDict):
    preferences_text: str
    preferences: dict
    itinerary: str
    activity_suggestions: str
    useful_links: list[dict]
    weather_forecast: str
    packing_list: str
    food_culture_info: str
    chat_history: Annotated[list[dict], "List of questions and answers"]
    user_question: str
    chat_response: str

# LangGraph
workflow = StateGraph(GraphState)
workflow.add_node("generate_itinerary", generate_itinerary.generate_itinerary)
workflow.add_node("recommend_activities", recommend_activities.recommend_activities)
workflow.add_node("fetch_useful_links", fetch_useful_links.fetch_useful_links)
workflow.add_node("weather_forecaster", weather_forecaster.weather_forecaster)
workflow.add_node("packing_list_generator", packing_list_generator.packing_list_generator)
workflow.add_node("food_culture_recommender", food_culture_recommender.food_culture_recommender)
workflow.add_node("chat_agent", chat_agent.chat_node)
workflow.set_entry_point("generate_itinerary")
workflow.add_edge("generate_itinerary", "recommend_activities")
workflow.add_edge("recommend_activities", "fetch_useful_links")
workflow.add_edge("fetch_useful_links", "weather_forecaster")
workflow.add_edge("weather_forecaster", "packing_list_generator")
workflow.add_edge("packing_list_generator", "food_culture_recommender")
workflow.add_edge("food_culture_recommender", "chat_agent")
workflow.add_edge("chat_agent", END)
graph = workflow.compile()

# ========== SIDEBAR IMPROVEMENTS START - LINE 95 ==========
with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    
    # Always show "Plan New Trip" button
    if st.button("🔄 Plan New Trip", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    # Check for trip data more safely
    has_trip_data = False
    trip_preferences = None
    
    try:
        if hasattr(st.session_state, 'state') and st.session_state.state:
            trip_preferences = st.session_state.state.get('preferences')
            if trip_preferences and isinstance(trip_preferences, dict) and trip_preferences.get('destination'):
                has_trip_data = True
    except:
        has_trip_data = False
    
    # Show trip-specific content only when we have valid trip data
    if has_trip_data and trip_preferences:
        st.markdown("---")
        st.markdown('<div class="trip-summary">', unsafe_allow_html=True)
        st.markdown("### 📊 Current Trip")
        st.markdown(f"**📍 Destination:** {trip_preferences.get('destination', 'N/A')}")
        st.markdown(f"**📅 Duration:** {trip_preferences.get('duration', 0)} days")
        st.markdown(f"**👥 People:** {trip_preferences.get('num_people', 'N/A')}")
        st.markdown(f"**💰 Budget:** {trip_preferences.get('budget_type', 'N/A')}")
        st.markdown(f"**🎯 Type:** {trip_preferences.get('holiday_type', 'N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export PDF button
        if st.button("📄 Export to PDF", use_container_width=True):
            itinerary_text = None
            try:
                itinerary_text = st.session_state.state.get("itinerary")
            except:
                pass
                
            if itinerary_text:
                try:
                    pdf_path = export_to_pdf(itinerary_text)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                "📥 Download PDF",
                                f.read(),
                                file_name="travel_itinerary.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        st.success("✅ PDF ready for download!")
                except Exception as e:
                    st.error(f"PDF export failed: {str(e)}")
            else:
                st.warning("Please generate an itinerary first!")
    
    # Always show help sections
    st.markdown("---")
    st.markdown("### ❓ How to Use")
    st.markdown("""
    1. **Fill the form** with your travel preferences
    2. **Generate itinerary** to get your base plan
    3. **Use buttons** to get additional details
    4. **Chat** to ask questions about your trip
    5. **Export PDF** when satisfied
    """)
    
    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    - Be specific about interests in comments
    - Try different budget types for varied options
    - Use chat for restaurant recommendations
    - Check weather before finalizing activities
    """)
# ========== SIDEBAR IMPROVEMENTS END ==========

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = {
        "preferences_text": "",
        "preferences": {},
        "itinerary": "",
        "activity_suggestions": "",
        "useful_links": [],
        "weather_forecast": "",
        "packing_list": "",
        "food_culture_info": "",
        "chat_history": [],
        "user_question": "",
        "chat_response": ""
    }

# NEW: Initialize user defaults for smart form filling
if "user_defaults" not in st.session_state:
    st.session_state.user_defaults = {}

# ========== ENHANCED FORM DESIGN START - LINE 165 ==========
# NEW: Enhanced form with better validation and styling
with st.form("travel_form"):
    st.markdown("### ✈️ Plan Your Perfect Trip")
    st.markdown("Fill in your travel preferences to get a personalized itinerary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📍 **Destination & Timing**")
        destination = st.text_input(
            "Destination", 
            placeholder="e.g., Paris, Tokyo, New York",
            help="Enter the city or country you want to visit"
        )
        
        # NEW: Form validation
        if not destination and st.session_state.get('form_submitted', False):
            st.error("⚠️ Please enter a destination")
        
        month = st.selectbox(
            "Month of Travel", 
            options=["January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"],
            help="Choose your travel month for weather-appropriate suggestions"
        )
        
        duration = st.number_input(
            "Duration (days)", 
            min_value=1, 
            max_value=30, 
            value=st.session_state.user_defaults.get('duration', 7),
            help="How many days will you be traveling?"
        )
        
        num_people = st.selectbox(
            "Number of People", 
            ["1", "2", "3", "4-6", "7-10", "10+"],
            index=st.session_state.user_defaults.get('num_people_idx', 1),
            help="This helps customize recommendations for your group size"
        )
        
    with col2:
        st.markdown("#### 🎯 **Travel Style & Budget**")
        holiday_type = st.selectbox(
            "Holiday Type", 
            ["Any", "Party", "Skiing", "Backpacking", "Family", "Beach", "Festival", 
             "Adventure", "City Break", "Romantic", "Cruise"],
            help="Choose the type of experience you're looking for"
        )
        
        budget_type = st.selectbox(
            "Budget Type", 
            ["Budget", "Mid-Range", "Luxury", "Backpacker", "Family"],
            index=st.session_state.user_defaults.get('budget_idx', 0),
            help="This affects accommodation and activity recommendations"
        )
        
        comments = st.text_area(
            "Additional Comments", 
            placeholder="Any specific preferences? (e.g., vegetarian food, museums, nightlife, accessibility needs)",
            height=100,
            help="The more specific you are, the better your recommendations will be!"
        )
    
    # NEW: Enhanced submit button with better styling
    st.markdown("---")
    col_submit = st.columns([1, 2, 1])
    with col_submit[1]:
        submit_button = st.form_submit_button(
            "🚀 Generate My Perfect Itinerary", 
            use_container_width=True
        )
    
    # ========== ENHANCED FORM PROCESSING START - LINE 225 ==========
    if submit_button:
        st.session_state['form_submitted'] = True
        
        # NEW: Form validation
        if not destination:
            st.error("⚠️ Please enter a destination before generating your itinerary!")
            st.stop()
        
        # NEW: Progress tracking
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # NEW: Save user defaults for next time
            st.session_state.user_defaults.update({
                'duration': duration,
                'num_people_idx': ["1", "2", "3", "4-6", "7-10", "10+"].index(num_people),
                'budget_idx': ["Budget", "Mid-Range", "Luxury", "Backpacker", "Family"].index(budget_type)
            })
        
        preferences_text = f"Destination: {destination}\nMonth: {month}\nDuration: {duration} days\nPeople: {num_people}\nType: {holiday_type}\nBudget: {budget_type}\nComments: {comments}"
        preferences = {
            "destination": destination,
            "month": month,
            "duration": duration,
            "num_people": num_people,
            "holiday_type": holiday_type,
            "budget_type": budget_type,
            "comments": comments
        }

        st.session_state.state.update({
            "preferences_text": preferences_text,
            "preferences": preferences,
            "chat_history": [],
            "user_question": "",
            "chat_response": "",
            "activity_suggestions": "",
            "useful_links": [],
            "weather_forecast": "",
            "packing_list": "",
            "food_culture_info": ""
        })

        # NEW: Enhanced progress tracking with status updates
        try:
            status_text.text("🔄 Initializing AI agents...")
            progress_bar.progress(10)
            
            status_text.text("🗺️ Generating your personalized itinerary...")
            progress_bar.progress(30)
            
            result = graph.invoke(st.session_state.state)
            
            status_text.text("✅ Processing recommendations...")
            progress_bar.progress(80)
            
            st.session_state.state.update(result)
            
            progress_bar.progress(100)
            status_text.text("🎉 Your itinerary is ready!")
            
            if result.get("itinerary"):
                st.success("🎉 **Itinerary generated successfully!** Scroll down to see your personalized travel plan.")
                st.balloons()  # NEW: Celebration animation
            else:
                st.error("😕 Failed to generate itinerary. Please try again with different parameters.")
                
        except Exception as e:
            st.error(f"❌ Error generating itinerary: {str(e)}")
            st.info("💡 **Troubleshooting tips:**\n- Check your internet connection\n- Try a different destination\n- Make sure Ollama is running")
# ========== ENHANCED FORM PROCESSING END ==========

# ========== ENHANCED RESULTS LAYOUT START - LINE 285 ==========
# Main layout for results
if st.session_state.state.get("itinerary"):
    # NEW: Success message with trip summary
    st.markdown("---")
    st.markdown("## 🎉 Your Personalized Travel Plan is Ready!")
    
    # NEW: Trip overview cards
    col_overview = st.columns(4)
    prefs = st.session_state.state["preferences"]
    
    with col_overview[0]:
        st.metric("📍 Destination", prefs.get('destination', 'N/A'))
    with col_overview[1]:
        st.metric("📅 Duration", f"{prefs.get('duration', 0)} days")
    with col_overview[2]:
        st.metric("👥 Travelers", prefs.get('num_people', 'N/A'))
    with col_overview[3]:
        st.metric("💰 Budget", prefs.get('budget_type', 'N/A'))
    
    st.markdown("---")
    
    # NEW: Responsive layout for itinerary and chat
    col_itin, col_chat = st.columns([2.5, 1.5])  # Better ratio for readability

    with col_itin:
        st.markdown("## 🗺️ Your Itinerary")
        
        # NEW: Itinerary in a styled container
        with st.container():
            st.markdown(st.session_state.state["itinerary"])

        st.markdown("---")
        st.markdown("### 🎯 Get Additional Recommendations")
        st.markdown("Click the buttons below to get more detailed information for your trip:")
        
        # ========== ENHANCED BUTTON LAYOUT START - LINE 315 ==========
        # NEW: Better responsive button layout (3x2 grid instead of 5x1)
        button_col1, button_col2, button_col3 = st.columns(3)
        
        with button_col1:
            activities_btn = st.button(
                "🎯 Activity Suggestions", 
                use_container_width=True,
                help="Get personalized activity recommendations based on your interests"
            )
            weather_btn = st.button(
                "🌤️ Weather Forecast", 
                use_container_width=True,
                help="Detailed weather information for your travel dates"
            )
        
        with button_col2:
            links_btn = st.button(
                "🔗 Useful Links", 
                use_container_width=True,
                help="Curated travel guides and resources for your destination"
            )
            culture_btn = st.button(
                "🍽️ Food & Culture", 
                use_container_width=True,
                help="Local cuisine recommendations and cultural etiquette tips"
            )
        
        with button_col3:
            packing_btn = st.button(
                "🎒 Packing List", 
                use_container_width=True,
                help="Customized packing checklist based on your trip details"
            )
            # NEW: Generate all button
            if st.button(
                "✨ Get All Details", 
                use_container_width=True,
                help="Generate all recommendations at once",
                type="primary"
            ):
                activities_btn = links_btn = weather_btn = packing_btn = culture_btn = True
        # ========== ENHANCED BUTTON LAYOUT END ==========

        # ========== ENHANCED RESULTS DISPLAY START - LINE 355 ==========
        # NEW: Process button clicks with loading states
        if activities_btn:
            with st.spinner("🔍 Finding amazing activities for you..."):
                result = recommend_activities.recommend_activities(st.session_state.state)
                st.session_state.state.update(result)
        
        if links_btn:
            with st.spinner("🔗 Gathering useful travel resources..."):
                result = fetch_useful_links.fetch_useful_links(st.session_state.state)
                st.session_state.state.update(result)
        
        if weather_btn:
            with st.spinner("🌤️ Checking weather conditions..."):
                result = weather_forecaster.weather_forecaster(st.session_state.state)
                st.session_state.state.update(result)
        
        if packing_btn:
            with st.spinner("🎒 Creating your packing checklist..."):
                result = packing_list_generator.packing_list_generator(st.session_state.state)
                st.session_state.state.update(result)
        
        if culture_btn:
            with st.spinner("🍽️ Discovering local culture and cuisine..."):
                result = food_culture_recommender.food_culture_recommender(st.session_state.state)
                st.session_state.state.update(result)

        # NEW: Tabbed interface for better organization
        st.markdown("---")
        if any([
            st.session_state.state.get("activity_suggestions"),
            st.session_state.state.get("useful_links"),
            st.session_state.state.get("weather_forecast"),
            st.session_state.state.get("packing_list"),
            st.session_state.state.get("food_culture_info")
        ]):
            st.markdown("### 📋 Your Additional Recommendations")
            
            # Create tabs for better organization
            available_tabs = []
            tab_contents = []
            
            if st.session_state.state.get("activity_suggestions"):
                available_tabs.append("🎯 Activities")
                tab_contents.append(("activity_suggestions", "Here are personalized activity recommendations:"))
            
            if st.session_state.state.get("useful_links"):
                available_tabs.append("🔗 Resources")
                tab_contents.append(("useful_links", "Helpful travel resources and guides:"))
            
            if st.session_state.state.get("weather_forecast"):
                available_tabs.append("🌤️ Weather")
                tab_contents.append(("weather_forecast", "Weather information for your trip:"))
            
            if st.session_state.state.get("packing_list"):
                available_tabs.append("🎒 Packing")
                tab_contents.append(("packing_list", "Your customized packing checklist:"))
            
            if st.session_state.state.get("food_culture_info"):
                available_tabs.append("🍽️ Culture")
                tab_contents.append(("food_culture_info", "Local food and cultural insights:"))
            
            if available_tabs:
                tabs = st.tabs(available_tabs)
                
                for i, (key, description) in enumerate(tab_contents):
                    with tabs[i]:
                        st.markdown(f"*{description}*")
                        if key == "useful_links":
                            # Special handling for links
                            links = st.session_state.state[key]
                            if links:
                                for link in links:
                                    st.markdown(f"🔗 [{link['title']}]({link['link']})")
                            else:
                                st.info("No links available yet. Click 'Get Useful Links' to fetch resources.")
                        else:
                            content = st.session_state.state[key]
                            if content:
                                st.markdown(content)
                            else:
                                st.info(f"Click the corresponding button above to get {key.replace('_', ' ')}.")
        # ========== ENHANCED RESULTS DISPLAY END ==========

    # ========== ENHANCED CHAT INTERFACE START - LINE 425 ==========
    with col_chat:
        # Enhanced chat header with trip info
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.2rem; border-radius: 20px 20px 0 0; 
                    text-align: center; color: white; margin-bottom: 0;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h3 style="margin: 0; font-size: 1.5rem; font-weight: 600;">💬 Your AI Travel Buddy</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.95;">
                Ask me anything about your {st.session_state.state['preferences'].get('destination', 'trip')} adventure! ✨
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced chat container
        st.markdown("""
        <div style="background: linear-gradient(145deg, #f8f9fb 0%, #e9ecef 100%); 
                    border-radius: 0 0 20px 20px; 
                    padding: 1.5rem; min-height: 400px; max-height: 500px; 
                    overflow-y: auto; border: 2px solid #e3e7f1;
                    box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);">
        """, unsafe_allow_html=True)
        
        # Chat messages with enhanced styling
        if st.session_state.state["chat_history"]:
            for i, chat in enumerate(st.session_state.state["chat_history"]):
                # User message with modern bubble design
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                                color: white; padding: 12px 18px; border-radius: 20px 20px 4px 20px; 
                                max-width: 80%; box-shadow: 0 3px 10px rgba(79, 172, 254, 0.3);
                                font-size: 0.95rem; line-height: 1.4;">
                        <strong>You:</strong> {chat['question']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # AI response with enhanced styling
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 15px 20px; border-radius: 20px 20px 20px 4px; 
                                max-width: 85%; box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                                font-size: 0.95rem; line-height: 1.5;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 1.2rem; margin-right: 8px;">🤖</span>
                            <strong style="font-size: 0.9rem; opacity: 0.9;">AI Travel Buddy</strong>
                        </div>
                        {chat['response']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Enhanced welcome message
            st.markdown("""
            <div style="text-align: center; padding: 2.5rem 1rem; color: #495057;">
                <div style="font-size: 4rem; margin-bottom: 1.5rem; 
                           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           background-clip: text;">🤖✈️</div>
                <h4 style="color: #333; margin-bottom: 1.5rem; font-weight: 600;">
                    Hey there, fellow traveler! 👋
                </h4>
                <p style="margin-bottom: 1.5rem; font-size: 1.05rem; color: #6c757d;">
                    I'm your AI travel buddy, and I'm super excited to help make your trip amazing!
                </p>
                <div style="background: white; padding: 1.5rem; border-radius: 15px; 
                           margin: 1.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
                    <p style="margin-bottom: 1rem; font-weight: 600; color: #495057;">💡 Try asking me:</p>
                    <div style="text-align: left; max-width: 280px; margin: 0 auto;">
                        <p style="margin: 0.7rem 0; color: #6c757d;">
                            <strong>🍽️ "Where should I eat in [area]?"</strong>
                        </p>
                        <p style="margin: 0.7rem 0; color: #6c757d;">
                            <strong>🌟 "What's a hidden gem to visit?"</strong>
                        </p>
                        <p style="margin: 0.7rem 0; color: #6c757d;">
                            <strong>💰 "How can I save money on day 3?"</strong>
                        </p>
                        <p style="margin: 0.7rem 0; color: #6c757d;">
                            <strong>🎒 "What should I pack for the weather?"</strong>
                        </p>
                    </div>
                </div>
                <p style="font-style: italic; color: #888; font-size: 0.9rem;">
                    Just type your question below and let's chat! 💬
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced chat input styling
        st.markdown("""
        <style>
        .stChatInput > div > div > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 30px !important;
            border: none !important;
            padding: 3px !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        }
        .stChatInput > div > div > div > div > div {
            background: white !important;
            border-radius: 27px !important;
            border: none !important;
        }
        .stChatInput input {
            border: none !important;
            border-radius: 27px !important;
            padding: 15px 25px !important;
            font-size: 16px !important;
            background: white !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }
        .stChatInput input::placeholder {
            color: #adb5bd !important;
            font-style: italic !important;
            font-size: 15px !important;
        }
        .stChatInput input:focus {
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Enhanced chat input with dynamic placeholder
        trip_destination = st.session_state.state['preferences'].get('destination', 'your destination')
        user_input = st.chat_input(
            f"Ask me about {trip_destination}... (e.g., 'Best rooftop bars?', 'Rainy day backup plans?', 'Local breakfast spots?')"
        )
        
        # Enhanced quick suggestion buttons with better styling
        st.markdown("**💡 Quick Questions:**")
        
        # CSS for better button styling
        st.markdown("""
        <style>
        .quick-question-btn {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 15px;
            padding: 8px 12px;
            margin: 4px;
            transition: all 0.3s ease;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .quick-question-btn:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        col_quick1, col_quick2 = st.columns(2)
        with col_quick1:
            if st.button("🍽️ Best local eats", use_container_width=True, key="quick_restaurant"):
                user_input = f"What are the best authentic restaurants in {trip_destination} that locals actually go to? I want the real experience, not tourist traps!"
            if st.button("💎 Hidden gems", use_container_width=True, key="quick_gems"):
                user_input = f"What are some amazing hidden gems or off-the-beaten-path places in {trip_destination} that most tourists miss?"
        
        with col_quick2:
            if st.button("💰 Money-saving tips", use_container_width=True, key="quick_budget"):
                user_input = f"How can I save money during my {trip_destination} trip without missing out on the good stuff?"
            if st.button("⏰ Perfect timing", use_container_width=True, key="quick_timing"):
                user_input = f"What's the best time of day to visit the main attractions in {trip_destination}? Any insider timing tips?"
        
        # Process chat input
        if user_input:
            st.session_state.state["user_question"] = user_input
            
            # Enhanced loading message
            with st.spinner("🤔 Let me think about that for your trip..."):
                result = chat_agent.chat_node(st.session_state.state)
                st.session_state.state.update(result)
            
            st.rerun()
    # ========== ENHANCED CHAT INTERFACE END ==========

# ========== ENHANCED EMPTY STATE START - LINE 465 ==========
else:
    # NEW: Better empty state with helpful guidance
    st.markdown("## 👋 Welcome to Your AI Travel Planner!")
    
    col_empty1, col_empty2, col_empty3 = st.columns([1, 2, 1])
    with col_empty2:
        st.markdown("""
        ### 🌟 What makes this special?
        
        **🤖 AI-Powered**: Get personalized itineraries created by advanced AI
        
        **🎯 Comprehensive**: Activities, weather, packing lists, and cultural tips
        
        **💬 Interactive**: Chat with AI to refine and customize your plans
        
        **📱 User-Friendly**: Beautiful interface that works on all devices
        
        ---
        
        ### 🚀 Ready to start?
        **Fill out the form above** with your travel preferences and let AI create your perfect itinerary!
        
        *Need inspiration? Try destinations like Paris, Tokyo, Barcelona, or New York!*
        """)
        
        # NEW: Sample itinerary showcase
        with st.expander("👀 See a sample itinerary"):
            st.markdown("""
            **Sample: 3-Day Paris Romantic Getaway**
            
            **Day 1**: Arrival & Exploration
            - Morning: Check-in and Seine River walk
            - Afternoon: Louvre Museum visit
            - Evening: Dinner at Bistro near Eiffel Tower
            
            **Day 2**: Romantic Paris
            - Morning: Montmartre and Sacré-Cœur
            - Afternoon: Luxembourg Gardens picnic
            - Evening: Seine dinner cruise
            
            **Day 3**: Culture & Departure
            - Morning: Notre-Dame area exploration
            - Afternoon: Shopping at Champs-Élysées
            - Evening: Farewell dinner in Le Marais
            
            *Plus: Weather forecasts, packing lists, cultural tips, and more!*
            """)
# ========== ENHANCED EMPTY STATE END ==========

# NEW: Footer with additional information
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🤖 Powered by AI • ✈️ Travel Smart • 🌍 Explore More</p>
    <p><small>Your AI Travel Assistant - Making trip planning effortless and enjoyable!</small></p>
</div>
""", unsafe_allow_html=True)