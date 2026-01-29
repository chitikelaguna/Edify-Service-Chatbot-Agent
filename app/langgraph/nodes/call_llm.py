from typing import Dict, Any
from app.langgraph.state import AgentState
from app.llm.formatter import ResponseFormatter
from app.db.audit_repo import AuditRepo
import logging

logger = logging.getLogger(__name__)

def call_llm_node(state: AgentState) -> Dict[str, Any]:
    """
    Calls LLM to format response.
    Persists errors to audit log.
    """
    try:
        context = state.get("retrieved_context")
        source = state.get("source_type", "general")
        query = state["user_message"]
        session_id = state.get("session_id")
        admin_id = state.get("admin_id", "anonymous")
        
        # If response already set, skip
        if state.get("response"):
            return {}

        # CONTEXT REQUIREMENT: LLM must have Edify context (except greetings handled by decide_source)
        # Check if context is None or empty
        is_context_empty = (
            context is None or 
            (isinstance(context, list) and len(context) == 0) or
            (isinstance(context, dict) and len(context) == 0)
        )
        
        # If no context and not a greeting, reject
        if is_context_empty:
            from app.langgraph.nodes.decide_source import is_greeting
            if not is_greeting(query):
                logger.warning(f"Blocked LLM call without context for query: {query[:100]}")
                return {
                    "response": "I can only answer questions related to Edify CRM, LMS, RMS, or internal documents."
                }

        formatter = ResponseFormatter()
        response = formatter.format_response(query, context, source)
        
        return {"response": response}

    except Exception as e:
        logger.error(f"Error calling LLM: {e}", exc_info=True)
        # Persist error to audit log
        try:
            audit = AuditRepo()
            audit.log_action(
                admin_id=admin_id,
                action="llm_error",
                details={
                    "error": str(e),
                    "source_type": state.get("source_type"),
                    "query": query[:100]
                },
                session_id=session_id
            )
        except:
            pass
        return {"response": "I encountered an error generating the response."}
