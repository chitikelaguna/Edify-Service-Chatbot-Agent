from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.audit_repo import AuditRepo
import logging

logger = logging.getLogger(__name__)

def fallback_node(state: AgentState) -> Dict[str, Any]:
    """
    Fallback node for unexpected errors.
    Persists fallback event to audit log.
    """
    try:
        session_id = state.get("session_id")
        admin_id = state.get("admin_id", "anonymous")
        
        # Audit log fallback
        audit = AuditRepo()
        audit.log_action(
            admin_id=admin_id,
            action="fallback_triggered",
            details={
                "session_id": session_id,
                "user_message": state.get("user_message", "")[:100]
            },
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error logging fallback: {e}")
    
    return {"response": "An unexpected error occurred. Please try again."}
