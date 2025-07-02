import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_llm():
    """
    Get LLM: Groq for deployment, Ollama for local development
    Simple two-option setup - no OpenAI dependency
    """
    
    # Check if Groq API key is available (for deployment)
    if os.getenv("GROQ_API_KEY"):
        try:
            from langchain_groq import ChatGroq
            print("🚀 Using Groq API with Llama 3 70B (Deployment Mode)")
            return ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-70b-8192",  # Excellent for travel planning
                temperature=0.7,
                max_tokens=1000,
                timeout=30,
                max_retries=2
            )
        except Exception as e:
            print(f"❌ Groq initialization failed: {e}")
            print("📝 Falling back to local Ollama...")
    
    # Fallback to local Ollama (for development)
    try:
        from langchain_community.chat_models import ChatOllama
        print("🏠 Using local Ollama (Development Mode)")
        return ChatOllama(
            model="llama3.2:3b-instruct-q4_K_M",
            base_url="http://localhost:11434",
            timeout=60
        )
    except Exception as e:
        print(f"❌ Ollama initialization failed: {e}")
        raise Exception("❌ No LLM available! Please either:\n1. Set GROQ_API_KEY for deployment, or\n2. Run Ollama locally for development")

def get_llm_info():
    """Get information about which LLM is being used"""
    if os.getenv("GROQ_API_KEY"):
        return {
            "provider": "Groq",
            "model": "Llama 3 70B",
            "cost": "Free (30K tokens/day)",
            "speed": "Ultra Fast",
            "mode": "Deployment"
        }
    else:
        return {
            "provider": "Ollama",
            "model": "Llama 3.2 3B", 
            "cost": "Free (Local)",
            "speed": "Medium",
            "mode": "Development"
        }

# Test function
def test_llm():
    """Test if LLM is working"""
    try:
        llm = get_llm()
        from langchain_core.messages import HumanMessage
        
        response = llm.invoke([HumanMessage(content="Say 'LLM is working!' if you can respond.")])
        print(f"✅ LLM Test Successful: {response.content[:50]}...")
        return True
    except Exception as e:
        print(f"❌ LLM Test Failed: {e}")
        return False

if __name__ == "__main__":
    # Test the LLM when run directly
    print("🧪 Testing LLM Configuration...")
    info = get_llm_info()
    print(f"Mode: {info['mode']} | Provider: {info['provider']} | Model: {info['model']}")
    test_llm()