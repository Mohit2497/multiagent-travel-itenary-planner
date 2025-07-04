# MultiAgents-with-Langgraph-Travel-Itinerary-Planner

Welcome to the **AI Travel Itinerary Planner**, a modular multi-agent system built with Streamlit, LangGraph, and multiple LLM providers. This application leverages multiple AI agents to generate personalized travel itineraries and provide additional travel-related insights based on user preferences. The system is designed for modularity, with agents split into individual scripts for maintainability and scalability.

* **Repository**: https://github.com/Mohit2497/multiagent-travel-itenary-planner
* **Application Link**: [AI Travel Itinerary Planner](https://multiagent-travel-itinerary-planner.streamlit.app/)

<img src="https://github.com/user-attachments/assets/f7d2c6b4-f5ee-4b61-b1d4-1e45299f134a" width="600" height="600">

## Overview

The AI Travel Itinerary Planner uses a LangGraph workflow to manage a set of agents that collaboratively process user inputs (e.g., destination, month, duration) to produce a detailed itinerary, activity suggestions, weather forecasts, packing lists, food/culture recommendations, useful links, and a chat interface. The system supports multiple LLM providers, including Groq (with `llama3-70b-8192` model), and local Ollama for flexible deployment options.

## Features

* Generate a detailed travel itinerary with daily plans, dining options, and downtime.
* Suggest unique local activities based on the itinerary and preferences.
* Fetch the top 5 travel guide links for the destination and month.
* Provide weather forecasts, packing lists, and food/culture recommendations.
* Offer a conversational chat to answer itinerary-related questions with intelligent fallback responses.
* Export the itinerary as a PDF.
* Interactive chat interface with quick question buttons and clear chat functionality.
* Form validation and enhanced error handling.
* Progress tracking during itinerary generation.

## Directory Structure


```
MultiAgents-with-Langgraph-Travel-Itinerary-Planner/
│
├── agents/
│   ├── __init__.py
│   ├── generate_itinerary.py
│   ├── recommend_activities.py
│   ├── fetch_useful_links.py
│   ├── weather_forecaster.py
│   ├── packing_list_generator.py
│   ├── food_culture_recommender.py
│   └── chat_agent.py
│
├── llm_helper.py
├── utils_export.py
├── travel_agent.py
├── requirements.txt
├── .env
└── README.md
```

* **agents/**: Contains individual Python scripts for each agent, modularizing the logic.
* **llm_helper.py**: LLM configuration and utility functions supporting multiple providers.
* **utils_export.py**: Houses shared utility functions (e.g., PDF export).
* **travel_agent.py**: The main Streamlit application file that orchestrates the workflow and UI.
* **requirements.txt**: Lists project dependencies.
* **.env**: Stores environment variables (e.g., API keys) - create this file.

## Setup Instructions

### Prerequisites

* Python 3.8 or higher.
* One of the following LLM providers:
  * **Groq API** account with access to `llama3-70b-8192` (Recommended for best performance)
  * **Ollama** installed locally with models like `llama3.2`
* A Google Serper API key for web search functionality.

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Mohit2497/multiagent-travel-itenary-planner.git
cd MultiAgents-with-Langgraph-Travel-Itinerary-Planner
```


2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the root directory and add your API keys:

```env
# Google Serper API for web search (Required)
SERPER_API_KEY=your_serper_api_key_here
```

### LLM Provider Setup

#### Option 1: Groq API (Recommended)

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Create an API key
4. Add the key to your `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
```

**Benefits of Groq:**
* Fast inference speed
* High-quality responses
* Cost-effective
* No local setup required

#### Option 2: Ollama (Local)

1. Install Ollama:

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from ollama.ai
```

2. Start Ollama and pull a model:

```bash
ollama serve
ollama pull llama3.2
```

3. Update your `.env` file:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

## Running the Application

1. Launch the Streamlit app:

```bash
streamlit run travel_agent.py
```

2. Open your browser and navigate to the provided URL (e.g., `http://localhost:8501`).

## Usage

### Planning Your Trip

* Enter your travel preferences in the form:
  * **Destination**: City or country you want to visit
  * **Month**: Travel month for weather-appropriate suggestions
  * **Duration**: Number of days (1-30)
  * **Number of People**: Group size for customized recommendations
  * **Holiday Type**: Trip style (Beach, Adventure, City Break, etc.)
  * **Budget Type**: Budget level (Budget, Mid-Range, Luxury, etc.)
  * **Additional Comments**: Specific preferences or requirements

* Click **"Generate My Perfect Itinerary"** to create a base plan.
* Use the **"Clear Form"** button to reset all fields and start fresh.

### Getting Additional Information

Use these buttons after generating an itinerary for more details:

* **Activity Suggestions**: Get personalized activity recommendations
* **Useful Links**: Find curated travel guides and resources
* **Weather Forecast**: Check detailed weather information
* **Packing List**: Get customized packing checklists
* **Food & Culture**: Learn about local cuisine and etiquette
* **Get All Details**: Generate all recommendations at once

### Using the Chat Interface

* Type questions in the chat input about your destination
* Use quick question buttons for common queries:
  * **Food**: Restaurant recommendations
  * **Gems**: Hidden attractions and local secrets
  * **Budget**: Money-saving tips and affordable options
  * **Timing**: Best times to visit attractions

* Use **"Clear Chat History"** to remove all chat messages

### Managing Your Plans

* **Export to PDF**: Download your complete itinerary
* **Plan New Trip**: Clear everything and start a new trip planning session
* **Current Trip Summary**: View trip details in the sidebar

## Key Features

### Multi-LLM Support

The application supports multiple LLM providers for flexibility:

* **Groq API**: Fast inference with `llama3-70b-8192` model (Recommended)
* **Ollama**: Local deployment for privacy and offline usage

### Chat Assistant

The chat interface provides intelligent responses for any destination worldwide:

* **Universal responses**: Works for any travel destination
* **Category detection**: Automatically identifies question types (food, budget, activities, etc.)
* **Fallback system**: Provides helpful responses even if the LLM fails
* **Quick actions**: Pre-defined buttons for common questions
* **Clear functionality**: Easy to clear chat history

### Enhanced UI

* **Responsive design**: Works on desktop and mobile devices
* **Modern styling**: Gradient themes and professional appearance
* **Progress tracking**: Visual feedback during itinerary generation
* **Form validation**: Prevents errors with proper input validation
* **Tab organization**: Organized display of additional recommendations

### Performance Tips

* **For best performance**: Use Groq API with `llama3-70b-8192`
* **For privacy**: Use Ollama with local models
* **For cost optimization**: Monitor API usage and set appropriate limits

## Requirements

```txt
streamlit>=1.28.0
langchain>=0.1.0
langchain-community>=0.0.20
langchain-groq>=0.1.0
langgraph>=0.0.30
python-dotenv>=1.0.0
requests>=2.31.0
google-search-results>=2.4.2
groq>=0.4.0
openai>=1.0.0
```

## API Keys Setup

### Google Serper API (Required)

1. Visit [Serper.dev](https://serper.dev)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add to your .env file

### Groq API (Recommended)

1. Visit [Groq Console](https://console.groq.com/)
2. Create an account
3. Generate an API key
4. Add to your .env file

**Why Groq?**
* Extremely fast inference (up to 750 tokens/second)
* Cost-effective pricing
* High-quality `llama3-70b-8192` model
* Reliable uptime and performance

## Contributing

Feel free to fork this repository, submit issues, or create pull requests to enhance the project. Contributions to improve agent logic, UI, add new LLM providers, or enhance the chat functionality are welcome!

## License

This project is open-source. See the LICENSE file for details (if applicable).

## Acknowledgements

* Built with Streamlit, LangGraph, LangChain, and multiple LLM providers.
* Thanks to the open-source community for tools and libraries!

## Contact

For questions or support, reach out to me on [LinkedIn](https://www.linkedin.com/in/deshpandem/) or open an issue in the repository.
