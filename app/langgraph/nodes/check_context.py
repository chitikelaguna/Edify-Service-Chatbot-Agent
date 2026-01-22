from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.retrieved_context_repo import RetrievedContextRepo
from app.db.audit_repo import AuditRepo
import logging

logger = logging.getLogger(__name__)

def check_context_node(state: AgentState) -> Dict[str, Any]:
    """
    Checks if retrieved_context has data.
    Handles greeting responses (source_type="none").
    Persists no-data-found events to database.
    """
    context = state.get("retrieved_context")
    source = state.get("source_type", "general")
    session_id = state.get("session_id")
    admin_id = state.get("admin_id", "anonymous")
    
    # If response already set (e.g., greeting), skip data checks
    if state.get("response"):
        # Don't store greetings in retrieved_context - they're not data retrievals
        # Greetings are handled by audit_logs if needed
        return {}
    
    # If general or none, we don't need context
    if source == "general" or source == "none":
        return {}
        
    if not context or (isinstance(context, list) and len(context) == 0):
        # No data found - persist this event
        try:
            context_repo = RetrievedContextRepo()
            query = state.get("user_message", "")
            context_repo.save_context(
                session_id=session_id or "unknown",
                admin_id=admin_id,
                source_type=source or "none",
                query_text=query,
                payload={"status": "no_data_found"},  # Only store status, query is in query_text column
                record_count=0,
                error_message="No data found"
            )
            
            # Audit log no data found
            audit = AuditRepo()
            audit.log_action(
                admin_id=admin_id,
                action="no_data_found",
                details={
                    "source_type": source,
                    "query": state.get("user_message", "")
                },
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error persisting no-data-found event: {e}")
        
        return {"response": "No relevant data found for your request.", "next_step": "end"}
        
    # Data found, proceed to LLM
    return {}
