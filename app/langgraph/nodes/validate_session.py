from typing import Dict, Any
from app.langgraph.state import AgentState
from app.core.security import validate_admin_session
from app.db.supabase import get_chatbot_supabase_client
from app.db.audit_repo import AuditRepo
import logging

logger = logging.getLogger(__name__)

def validate_session_node(state: AgentState) -> Dict[str, Any]:
    """
    Validates if the session is active.
    Persists validation failures to audit log.
    """
    session_id = state.get("session_id")
    admin_id = state.get("admin_id", "unknown")
    
    try:
        # We can reuse the core logic or re-implement for node context (no Depends)
        supabase = get_chatbot_supabase_client()
        response = (
            supabase.table("admin_sessions")
            .select("status")
            .eq("session_id", session_id)
            .single()
            .execute()
        )
        
        if not response.data:
            # Audit log session not found
            try:
                audit = AuditRepo()
                audit.log_action(
                    admin_id=admin_id,
                    action="session_not_found",
                    details={"session_id": session_id},
                    session_id=session_id
                )
            except:
                pass
            return {"response": "Session not found.", "next_step": "end"}
             
        if response.data["status"] != "active":
            # Audit log inactive session
            try:
                audit = AuditRepo()
                audit.log_action(
                    admin_id=admin_id,
                    action="session_inactive",
                    details={"session_id": session_id, "status": response.data["status"]},
                    session_id=session_id
                )
            except:
                pass
            return {"response": "Session is not active.", "next_step": "end"}

    except Exception as e:
        logger.error(f"Session validation failed: {e}", exc_info=True)
        # Audit log validation error
        try:
            audit = AuditRepo()
            audit.log_action(
                admin_id=admin_id,
                action="session_validation_error",
                details={"error": str(e), "session_id": session_id},
                session_id=session_id
            )
        except:
            pass
        return {"response": "System error during session validation.", "source_type": "error"}

    # No state change needed if valid, just proceed
    return {}
