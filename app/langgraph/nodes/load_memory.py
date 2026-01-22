from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.memory_repo import MemoryRepo
import logging

logger = logging.getLogger(__name__)

def load_memory_node(state: AgentState) -> Dict[str, Any]:
    """
    Loads conversation history into state.
    """
    try:
        session_id = state["session_id"]
        repo = MemoryRepo()
        history = repo.get_chat_history(session_id, limit=10)
        
        return {"conversation_history": history}
        
    except Exception as e:
        logger.error(f"Error loading memory: {e}")
        # Non-critical, can proceed with empty history? 
        # Or return error. Let's return empty.
        return {"conversation_history": []}
