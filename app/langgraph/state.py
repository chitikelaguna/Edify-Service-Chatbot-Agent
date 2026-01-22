from typing import List, Dict, Any, Optional, TypedDict
import operator

class AgentState(TypedDict):
    """
    State model for Edify Admin AI Chatbot.
    """
    session_id: str
    admin_id: str
    user_message: str
    conversation_history: List[Dict[str, str]]
    retrieved_context: Optional[Any]
    source_type: Optional[str]
    response: Optional[str]
