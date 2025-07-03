import streamlit as st
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
import os
from agents import generate_itinerary, recommend_activities, fetch_useful_links, weather_forecaster, packing_list_generator, food_culture_recommender, chat_agent
from llm_helper import get_llm, get_llm_info
from utils_export import export_to_pdf

# ========== LOAD ENVIRONMENT VARIABLES ==========
load_dotenv()

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="AI Travel Planner", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS STYLING ==========
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    /* Metric container styling */
    .metric-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    /* Button styling */
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
    
    /* Trip summary styling */
    .trip-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Form button styling */
    .stForm button[kind="primary"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stForm button[kind="secondary"] {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 25px;
        color: #6c757d;
        font-weight: 600;
    }
    
    /* Fix bottom spacing */
    .main .block-container {
        padding-bottom: 1rem !important;
    }
    
    .stApp > div:last-child {
        padding-bottom: 0 !important;
    }
    
    footer {
        display: none !important;
    }
    
    /* Chat button styling */
    .stButton > button {
        background: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 500;
        transition: all 0.2s;
        height: auto;
        white-space: normal;
        word-wrap: break-word;
    }
    
    .stButton > button:hover {
        background: #4A90E2;
        color: white;
        border-color: #4A90E2;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# ========== MAIN HEADER ==========
st.markdown("""
<div class="main-header">
    <h1>🌍 AI Travel Planner ✈️</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Create your perfect itinerary with AI-powered recommendations</p>
</div>
""", unsafe_allow_html=True)

# ========== INITIALIZE LLM AND APIs ==========
try:
    llm = get_llm()
    llm_info = get_llm_info()
    st.sidebar.info(f"🤖 {llm_info['provider']} ({llm_info['model']}) - {llm_info['mode']} Mode")
except Exception as e:
    st.error(f"Error initializing Ollama model: {e}")
    st.stop()

try:
    search = GoogleSerperAPIWrapper(api_key=os.getenv("SERPER_API_KEY"))
except Exception as e:
    st.error(f"Error initializing Google Serper API: {e}")
    st.stop()

# ========== DEFINE STATE GRAPH ==========
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

# ========== SETUP LANGGRAPH WORKFLOW ==========
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

# ========== SIDEBAR CONFIGURATION ==========
with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    
    # Plan New Trip button with enhanced clearing
    if st.button("🔄 Plan New Trip", use_container_width=True):
        # Clear ALL session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinitialize main state
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
        
        st.success("🎉 Ready for your next adventure!")
        st.info("👇 Fill out the form below to start planning!")
        st.rerun()
    
    # Check for trip data safely
    has_trip_data = False
    trip_preferences = None
    
    try:
        if hasattr(st.session_state, 'state') and st.session_state.state:
            trip_preferences = st.session_state.state.get('preferences')
            if trip_preferences and isinstance(trip_preferences, dict) and trip_preferences.get('destination'):
                has_trip_data = True
    except:
        has_trip_data = False
    
    # Show trip-specific content when we have valid trip data
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

# ========== INITIALIZE SESSION STATE ==========
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

if "user_defaults" not in st.session_state:
    st.session_state.user_defaults = {}

# ========== TRAVEL PLANNING FORM ==========
with st.form("travel_form"):
    st.markdown("### ✈️ Plan Your Perfect Trip")
    st.markdown("Fill in your travel preferences to get a personalized itinerary")
    
    # Form layout with two columns
    col1, col2 = st.columns(2)
    
    # Left column - Destination & Timing
    with col1:
        st.markdown("#### 📍 **Destination & Timing**")
        
        destination = st.text_input(
            "Destination", 
            placeholder="e.g., Paris, Tokyo, New York",
            help="Enter the city or country you want to visit"
        )
        
        # Form validation
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
    
    # Right column - Travel Style & Budget
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
    
    # Enhanced button section with both Generate and Clear buttons
    st.markdown("---")
    st.markdown('<div style="text-align: center;"><h4 style="color: #667eea;">🎯 Ready to Plan?</h4></div>', unsafe_allow_html=True)
    
    # Two buttons side by side with proper alignment
    col_btn_left, col_btn_generate, col_btn_clear, col_btn_right = st.columns([0.5, 2.5, 1.5, 0.5])
    
    with col_btn_generate:
        submit_button = st.form_submit_button(
            "🚀 Generate My Perfect Itinerary", 
            use_container_width=True,
            type="primary"
        )
    
    with col_btn_clear:
        clear_button = st.form_submit_button(
            "🗑️ Clear Form", 
            use_container_width=True,
            type="secondary"
        )

# ========== HANDLE CLEAR BUTTON ==========
if clear_button:
    # Clear all session state
    st.session_state.clear()
    
    # Reinitialize main state
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
    
    # Success message
    st.success("✅ Form cleared! Ready for a new adventure.")
    st.rerun()

# ========== HANDLE GENERATE ITINERARY BUTTON ==========
if submit_button:
    st.session_state['form_submitted'] = True
    
    # Form validation
    if not destination:
        st.error("⚠️ Please enter a destination before generating your itinerary!")
        st.stop()
    
    # Progress tracking
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Save user defaults for next time
        st.session_state.user_defaults.update({
            'duration': duration,
            'num_people_idx': ["1", "2", "3", "4-6", "7-10", "10+"].index(num_people),
            'budget_idx': ["Budget", "Mid-Range", "Luxury", "Backpacker", "Family"].index(budget_type)
        })
    
    # Create preferences text and dictionary
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

    # Update session state
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

    # Generate itinerary with progress tracking
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
            st.balloons()
        else:
            st.error("😕 Failed to generate itinerary. Please try again with different parameters.")
            
    except Exception as e:
        st.error(f"❌ Error generating itinerary: {str(e)}")
        st.info("💡 **Troubleshooting tips:**\n- Check your internet connection\n- Try a different destination\n- Make sure Ollama is running")

# ========== RESULTS LAYOUT ==========
if st.session_state.state.get("itinerary"):
    # Success message with trip summary
    st.markdown("---")
    st.markdown("## 🎉 Your Personalized Travel Plan is Ready!")
    
    # Trip overview cards
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
    
    # Responsive layout for itinerary and chat
    col_itin, col_chat = st.columns([2.5, 1.5])

    # ========== ITINERARY SECTION ==========
    with col_itin:
        st.markdown("## 🗺️ Your Itinerary")
        
        # Display itinerary in a styled container
        with st.container():
            st.markdown(st.session_state.state["itinerary"])

        st.markdown("---")
        st.markdown("### 🎯 Get Additional Recommendations")
        st.markdown("Click the buttons below to get more detailed information for your trip:")
        
        # Additional recommendation buttons (3x2 grid)
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
            # Generate all button
            if st.button(
                "✨ Get All Details", 
                use_container_width=True,
                help="Generate all recommendations at once",
                type="primary"
            ):
                activities_btn = links_btn = weather_btn = packing_btn = culture_btn = True

        # Process button clicks with loading states
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

        # Tabbed interface for additional recommendations
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

    # ========== CHAT SECTION ==========
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
        
        # Chat container with dynamic height
        if st.session_state.state["chat_history"]:
            container_height = "300px"
        else:
            container_height = "120px"  # Compact empty state
        
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
        
        # Display chat messages or welcome message
        if st.session_state.state["chat_history"]:
            for i, chat in enumerate(st.session_state.state["chat_history"]):
                # User message (right side, blue)
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
                        box-shadow: 0 2px 8px rgba(0,123,255,0.2);
                        word-wrap: break-word;
                        text-align: left;
                    ">
                        <strong>You:</strong> {chat['question']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # AI response (left side, green)
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
                        box-shadow: 0 2px 8px rgba(40,167,69,0.2);
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
            # Compact welcome message
            st.markdown("""
            <div style="text-align: center; padding: 8px;">
                <div style="font-size: 24px; margin-bottom: 5px;">🤖</div>
                <h5 style="color: #495057; margin-bottom: 5px; font-size: 14px;">Ready to help!</h5>
                <p style="color: #6c757d; font-size: 11px; margin-bottom: 8px;">
                    Ask about restaurants, activities, or travel tips!
                </p>
                <div style="background: white; padding: 6px; border-radius: 6px; font-size: 10px; color: #6c757d;">
                    💡 Try: "Best local food?" or "Money-saving tips?"
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
        
        # Quick question buttons
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
        
        # Clear Chat Button (only show when there are messages)
        if st.session_state.state.get("chat_history") and len(st.session_state.state["chat_history"]) > 0:
            st.markdown("---")
            
            col_clear_left, col_clear_center, col_clear_right = st.columns([1, 2, 1])
            
            with col_clear_center:
                if st.button(
                    "🗑️ Clear Chat History", 
                    use_container_width=True, 
                    key="clear_chat_history",
                    type="secondary"
                ):
                    st.session_state.state["chat_history"] = []
                    st.session_state.state["user_question"] = ""
                    st.session_state.state["chat_response"] = ""
                    st.success("✅ Chat cleared successfully!")
                    st.rerun()
        
        # ========== CHAT PROCESSING ==========
        if user_input:
            st.session_state.state["user_question"] = user_input
            
            with st.spinner("🤔 Thinking..."):
                try:
                    # Import and call chat agent from agents folder
                    from agents import chat_agent
                    result = chat_agent.chat_node(st.session_state.state)
                    st.session_state.state.update(result)
                    
                    response = result.get('chat_response', '')
                    if len(response) > 20 and "technical" not in response.lower():
                        st.success("✅ Got a great response!")
                    
                except Exception as e:
                    st.error(f"❌ Chat error: {str(e)}")
                    
                    # Fallback response
                    def create_manual_fallback(question, destination):
                        q = question.lower()
                        if 'restaurant' in q or 'food' in q:
                            return f"🍽️ For great food in {destination}: Look for busy local restaurants where residents eat, ask hotel staff for their personal recommendations, and try traditional dishes specific to the region!"
                        elif 'money' in q or 'save' in q or 'budget' in q:
                            return f"💰 Save money in {destination}: Stay in local neighborhoods vs tourist areas, eat where locals eat, use public transport, and look for free activities like parks and markets!"
                        elif 'hidden' in q or 'gem' in q:
                            return f"💎 Hidden gems in {destination}: Explore residential neighborhoods, visit local markets early morning, and ask shopkeepers about favorite spots off the beaten path!"
                        elif 'time' in q or 'timing' in q:
                            return f"⏰ Best timing for {destination}: Visit popular attractions early morning or late afternoon, and weekdays are generally less crowded than weekends!"
                        else:
                            return f"✨ Great question about {destination}! For detailed local insights, I recommend asking locals when you arrive and checking recent travel forums."
                    
                    fallback_response = create_manual_fallback(user_input, trip_destination)
                    chat_entry = {"question": user_input, "response": fallback_response}
                    
                    if "chat_history" not in st.session_state.state:
                        st.session_state.state["chat_history"] = []
                    st.session_state.state["chat_history"].append(chat_entry)
            
            st.rerun()

# ========== EMPTY STATE ==========
else:
    # Welcome message when no itinerary is generated
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
        
        # Sample itinerary showcase
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

# ========== FOOTER ==========
st.markdown("""
<div style="text-align: center; color: #999; font-size: 11px; padding: 5px 0; margin-top: 15px;">
    🤖 AI Travel Assistant
</div>
""", unsafe_allow_html=True)