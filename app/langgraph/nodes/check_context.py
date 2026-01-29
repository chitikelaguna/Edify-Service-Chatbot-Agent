from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.retrieved_context_repo import RetrievedContextRepo
from app.db.audit_repo import AuditRepo
from app.langgraph.nodes.decide_source import is_greeting
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
    user_message = state.get("user_message", "")
    
    # If response already set (e.g., greeting), skip data checks
    if state.get("response"):
        # Don't store greetings in retrieved_context - they're not data retrievals
        # Greetings are handled by audit_logs if needed
        return {}
    
    # HARD GATE: Block "general" queries that are not greetings
    if source == "general":
        if not is_greeting(user_message):
            logger.warning(f"Blocked general knowledge query: {user_message[:100]}")
            return {
                "response": "I can only answer questions related to Edify CRM, LMS, RMS, or internal documents."
            }
        # If it's a greeting, allow it to pass (greetings are handled by decide_source)
        return {}
    
    # If none, we don't need context (greetings set source_type="none")
    if source == "none":
        return {}
        
    if not context or (isinstance(context, list) and len(context) == 0):
        # No data found - this should be rare for valid CRM/LMS/RMS/RAG intents
        # Log this as it indicates a potential issue with data retrieval
        query = state.get("user_message", "")
        logger.warning(f"No data found for {source} query: {query[:100]}")
        
        # Persist this event for analysis
        try:
            context_repo = RetrievedContextRepo()
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
                    "query": query
                },
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error persisting no-data-found event: {e}")
        
        # Return user-friendly message
        # Note: With improved intent detection, this should rarely occur for valid CRM queries
        return {"response": "I couldn't find any data matching your request. Please try rephrasing or check if the data exists in the system.", "next_step": "end"}
        
    # Data found, proceed to LLM
    return {}
