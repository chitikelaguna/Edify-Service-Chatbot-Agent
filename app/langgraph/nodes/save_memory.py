from typing import Dict, Any
from app.langgraph.state import AgentState
import logging

logger = logging.getLogger(__name__)

def save_memory_node(state: AgentState) -> Dict[str, Any]:
    """
    DEPRECATED: This node is kept for backward compatibility but does nothing.
    Chat history is now saved in ChatService.process_user_message() as pairs in chat_history table.
    
    This node exists because the graph still references it, but the actual saving
    happens in ChatService after the full conversation pair is complete.
    """
    # Chat history is saved in ChatService, not here
    # This node is kept to maintain graph structure
    logger.debug("save_memory_node called (deprecated - chat_history saved in ChatService)")
    return {}
