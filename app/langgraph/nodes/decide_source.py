from typing import Dict, Any
from app.langgraph.state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Greeting keywords for detection
GREETING_KEYWORDS = [
    "hi", "hello", "hey", "hii", "hiii", "hiiii",
    "good morning", "good afternoon", "good evening",
    "morning", "afternoon", "evening",
    "greetings", "greeting",
    "hi there", "hello there", "hey there"
]

def is_greeting(message: str) -> bool:
    """
    Detects if a message is a greeting.
    Case-insensitive, trims whitespace.
    """
    if not message:
        return False
    
    # Normalize: lowercase, trim whitespace
    normalized = message.strip().lower()
    
    # Check exact match or starts with greeting keyword
    for keyword in GREETING_KEYWORDS:
        if normalized == keyword or normalized.startswith(keyword + " "):
            return True
    
    return False

def get_greeting_response() -> str:
    """
    Returns a friendly, professional greeting response.
    """
    return "Hii 👋\nWhat's up? How can I help you today?"

def decide_source_node(state: AgentState) -> Dict[str, Any]:
    """
    Decides which data source to query based on user_message.
    Detects greetings first (no LLM call needed).
    """
    try:
        user_message = state["user_message"]
        
        # Check for greeting first (no LLM call needed)
        if is_greeting(user_message):
            logger.info("Greeting detected, skipping data retrieval")
            return {
                "source_type": "none",
                "response": get_greeting_response()
            }
        
        # Not a greeting, use LLM to classify
        llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o")
        
        system_prompt = """You are a router. Classify the user's request.
        Categories:
        - "crm": Customer/Deal/Lead/Company data
        - "lms": Course/Training/Instructor data
        - "rms": Candidate/Job/Recruitment data
        - "rag": Policy/Knowledge base/Documents
        - "general": Off-topic or unclear requests
        
        Return ONLY the category name.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"input": user_message})
        source = result.content.strip().lower()
        
        valid_sources = ["crm", "lms", "rms", "rag", "general"]
        if source not in valid_sources:
            source = "general"
            
        logger.info(f"Decided source: {source}")
        
        return {"source_type": source}
        
    except Exception as e:
        logger.error(f"Error in decide_source: {e}", exc_info=True)
        return {"source_type": "general"} # Default to general to avoid crash
