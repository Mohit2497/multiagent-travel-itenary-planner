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

            # Complete Chat Interface Replacement
    # Replace the entire chat section in your travel_agent.py (around line 425)

    # ========== FIXED CHAT INTERFACE START ==========

    # ========== WORKING CHAT INTERFACE ==========
    with col_chat:
        # Chat header
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%); 
            padding: 15px; 
            border-radius: 12px 12px 0 0; 
            text-align: center; 
            color: white; 
            margin-bottom: 0;
            border: 1px solid #357ABD;
        ">
            <h3 style="margin: 0; font-size: 18px; font-weight: 600;">💬 Chat with AI Travel Buddy</h3>
            <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">
                Ask me anything about your trip to {st.session_state.state['preferences'].get('destination', 'your destination')}!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat container
        if st.session_state.state["chat_history"]:
            container_height = "100px"
        else:
            container_height = "80px"
        
        # Chat messages display
        st.markdown(f"""
        <div style="
            background: #f8f9fa; 
            border: 1px solid #357ABD;
            border-top: none;
            height: {container_height}; 
            overflow-y: auto; 
            padding: 15px;
            border-radius: 0 0 12px 12px;
            margin-bottom: 15px;
        " id="chat-messages">
        """, unsafe_allow_html=True)
        
        # Display messages or welcome
        if st.session_state.state["chat_history"]:
            for i, chat in enumerate(st.session_state.state["chat_history"]):
                # User message
                st.markdown(f"""
                <div style="margin-bottom: 15px; text-align: right;">
                    <div style="
                        display: inline-block;
                        background: #007bff;
                        color: white;
                        padding: 12px 16px;
                        border-radius: 18px 18px 4px 18px;
                        max-width: 80%;
                        font-size: 14px;
                        line-height: 1.4;
                        word-wrap: break-word;
                        text-align: left;
                    ">
                        <strong>You:</strong> {chat['question']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # AI response
                st.markdown(f"""
                <div style="margin-bottom: 15px; text-align: left;">
                    <div style="
                        display: inline-block;
                        background: #28a745;
                        color: white;
                        padding: 12px 16px;
                        border-radius: 18px 18px 18px 4px;
                        max-width: 85%;
                        font-size: 14px;
                        line-height: 1.5;
                        word-wrap: break-word;
                    ">
                        <div style="margin-bottom: 5px;">
                            <span style="font-size: 16px;">🤖</span>
                            <strong style="font-size: 12px; margin-left: 5px;">AI Travel Buddy</strong>
                        </div>
                        {chat['response']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Welcome message
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 48px; margin-bottom: 15px;">🤖✈️</div>
                <h4 style="color: #495057; margin-bottom: 15px; font-size: 16px;">
                    Hi! I'm your AI Travel Buddy! 👋
                </h4>
                <p style="color: #6c757d; font-size: 14px; margin-bottom: 15px;">
                    Ask me about restaurants, activities, money-saving tips, or anything about your trip!
                </p>
                <div style="background: white; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6;">
                    <p style="margin-bottom: 10px; font-weight: 600; color: #495057; font-size: 13px;">
                        💡 Try asking:
                    </p>
                    <div style="font-size: 12px; color: #6c757d;">
                        <p style="margin: 5px 0;">• "Best local restaurants?"</p>
                        <p style="margin: 5px 0;">• "How to save money?"</p>
                        <p style="margin: 5px 0;">• "Hidden gems to visit?"</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chat input
        trip_destination = st.session_state.state['preferences'].get('destination', 'your destination')
        user_input = st.chat_input(
            f"Ask about {trip_destination}...",
            key="travel_chat_input"
        )
        
        # Quick buttons
        st.markdown("**💡 Quick Questions:**")
        col_q1, col_q2 = st.columns(2)
        
        with col_q1:
            if st.button("🍽️ Food", use_container_width=True, key="q_food"):
                user_input = f"What are the best local restaurants in {trip_destination}?"
            if st.button("💎 Gems", use_container_width=True, key="q_gems"):
                user_input = f"What are hidden gems in {trip_destination}?"
        
        with col_q2:
            if st.button("💰 Budget", use_container_width=True, key="q_money"):
                user_input = f"How to save money in {trip_destination}?"
            if st.button("⏰ Timing", use_container_width=True, key="q_timing"):
                user_input = f"Best times to visit attractions in {trip_destination}?"

        if st.session_state.state.get("chat_history") and len(st.session_state.state["chat_history"]) > 0:
                st.markdown("---")  # Visual separator line
                
                # Create centered button layout
                col_left, col_center, col_right = st.columns([1, 2, 1])
                
                with col_center:
                    if st.button(
                        "🗑️ Clear Chat History", 
                        use_container_width=True, 
                        key="clear_chat_button",
                        type="secondary",
                        help="Clear all chat messages"
                    ):
                        # Clear all chat data
                        st.session_state.state["chat_history"] = []
                        st.session_state.state["user_question"] = ""
                        st.session_state.state["chat_response"] = ""
                        
                        # Show success message
                        st.success("✅ Chat history cleared!")
                        
                        # Refresh the page to update UI
                        st.rerun()       
        
        # ========== CRITICAL CHAT PROCESSING FIX ==========
        if user_input:
            st.session_state.state["user_question"] = user_input
            
            with st.spinner("🤔 Thinking..."):
                try:
                    print(f"🔄 Processing: {user_input}")
                    print(f"📍 Destination: {st.session_state.state['preferences'].get('destination')}")
                    
                    # DIRECT IMPORT AND CALL - This is the key fix!
                    import sys
                    import os
                    
                    # Add current directory to path if needed
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    if current_dir not in sys.path:
                        sys.path.append(current_dir)
                    
                    # Import chat_agent directly
                    from agents import chat_agent
                    
                    # Call the chat function directly
                    result = chat_agent.chat_node(st.session_state.state)
                    
                    # Update state
                    st.session_state.state.update(result)
                    
                    # Check response quality
                    response = result.get('chat_response', '')
                    print(f"✅ Response: {response[:100]}...")
                    
                    if len(response) > 20:
                        st.success("✅ Got a great response!")
                    else:
                        st.warning("⚠️ Response might be too short")
                    
                except ImportError as e:
                    st.error("❌ Cannot find chat_agent.py file!")
                    st.info("💡 Make sure chat_agent.py is in the same folder as travel_agent.py")
                    print(f"Import error: {e}")
                    
                    # Manual fallback
                    fallback_response = create_manual_fallback(user_input, trip_destination)
                    add_to_chat_history(user_input, fallback_response)
                    
                except Exception as e:
                    st.error(f"❌ Chat error: {str(e)}")
                    print(f"Error details: {e}")
                    
                    # Manual fallback
                    fallback_response = create_manual_fallback(user_input, trip_destination)
                    add_to_chat_history(user_input, fallback_response)
            
            # Refresh page to show new message
            st.rerun()

            # ========== HELPER FUNCTIONS ==========
            def create_manual_fallback(question, destination):
                """Create fallback responses when chat_agent fails"""
                q = question.lower()
                
                if 'restaurant' in q or 'food' in q or 'eat' in q:
                    return f"🍽️ For great food in {destination}: Look for busy local restaurants where residents eat, ask hotel staff for their personal recommendations, and try traditional dishes specific to the region. Street food from popular vendors is usually delicious and authentic!"
                
                elif 'money' in q or 'save' in q or 'budget' in q or 'cheap' in q:
                    return f"💰 Save money in {destination}: Stay in local neighborhoods vs tourist areas, eat where locals eat, use public transport, look for free activities like parks and markets, and ask about student/group discounts at attractions!"
                
                elif 'hidden' in q or 'gem' in q or 'secret' in q or 'local' in q:
                    return f"💎 Hidden gems in {destination}: Explore residential neighborhoods, visit local markets early morning, ask shopkeepers about favorite spots, and wander off main tourist paths. Often the best experiences aren't in guidebooks!"
                
                elif 'time' in q or 'when' in q or 'timing' in q or 'best' in q:
                    return f"⏰ Best timing for {destination}: Visit popular attractions early morning or late afternoon, weekdays are less crowded than weekends, and ask locals about specific timing for places you want to visit!"
                
                elif 'transport' in q or 'taxi' in q or 'bus' in q or 'getting around' in q:
                    return f"🚗 Getting around {destination}: Public transport is usually cheapest, download local transport apps, ask locals for directions, and consider walking for short distances - you'll discover more!"
                
                else:
                    return f"✨ Great question about {destination}! For detailed local insights, I recommend asking locals when you arrive, checking recent travel forums, and being open to spontaneous discoveries during your trip!"

            def add_to_chat_history(question, response):
                """Add message to chat history"""
                chat_entry = {"question": question, "response": response}
                
                if "chat_history" not in st.session_state.state:
                    st.session_state.state["chat_history"] = []
                
                st.session_state.state["chat_history"].append(chat_entry)

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