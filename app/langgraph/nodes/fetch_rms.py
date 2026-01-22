from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.rms_repo import RMSRepo
from app.db.retrieved_context_repo import RetrievedContextRepo
import logging

logger = logging.getLogger(__name__)

def fetch_rms_node(state: AgentState) -> Dict[str, Any]:
    """
    Fetches RMS data from Supabase and attaches to state.
    Sets source_type to 'rms' and attaches data to retrieved_context.
    Persists retrieved data to database.
    Never calls LLM - only data retrieval.
    """
    try:
        query = state["user_message"]
        session_id = state["session_id"]
        logger.info(f"Fetching RMS data for query: {query[:50]}...")
        
        import time
        retrieval_start = time.time()
        repo = RMSRepo()
        data = repo.search_rms(query)
        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
        
        # Persist retrieved context to database
        context_repo = RetrievedContextRepo()
        admin_id = state.get("admin_id", "anonymous")
        context_repo.save_context(
            session_id=session_id,
            admin_id=admin_id,
            source_type="rms",
            query_text=query,
            payload={"data": data if data else []},  # Only store retrieved data, not query
            record_count=len(data) if data else 0,
            retrieval_time_ms=retrieval_time_ms
        )
        
        # Return empty list if no data (not None) - let check_context handle fallback
        return {
            "retrieved_context": data if data else [],
            "source_type": "rms"
        }
        
    except Exception as e:
        logger.error(f"Error fetching RMS: {e}", exc_info=True)
        # Persist error context
        try:
            context_repo = RetrievedContextRepo()
            admin_id = state.get("admin_id", "anonymous")
            query = state.get("user_message", "")
            context_repo.save_context(
                session_id=state.get("session_id", "unknown"),
                admin_id=admin_id,
                source_type="rms",
                query_text=query,
                payload={"error": str(e)},  # Only store error, query is in query_text column
                record_count=0,
                error_message=str(e)
            )
        except:
            pass
        # Return empty context - check_context node will handle fallback
        return {
            "retrieved_context": [],
            "source_type": "rms"
        }
