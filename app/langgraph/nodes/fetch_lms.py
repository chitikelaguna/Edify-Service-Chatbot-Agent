from typing import Dict, Any
from app.langgraph.state import AgentState
from app.db.lms_repo import LMSRepo
from app.db.retrieved_context_repo import RetrievedContextRepo
import logging

logger = logging.getLogger(__name__)

def fetch_lms_node(state: AgentState) -> Dict[str, Any]:
    """
    Fetches LMS data from Supabase and attaches to state.
    Sets source_type to 'lms' and attaches data to retrieved_context.
    Persists retrieved data to database.
    Never calls LLM - only data retrieval.
    """
    try:
        query = state["user_message"]
        session_id = state["session_id"]
        logger.info(f"Fetching LMS data for query: {query[:50]}...")
        
        import time
        retrieval_start = time.time()
        repo = LMSRepo()
        data = repo.search_lms(query)
        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
        
        # Persist retrieved context to database
        context_repo = RetrievedContextRepo()
        admin_id = state.get("admin_id", "anonymous")
        context_repo.save_context(
            session_id=session_id,
            admin_id=admin_id,
            source_type="lms",
            query_text=query,
            payload={"data": data if data else []},  # Only store retrieved data, not query
            record_count=len(data) if data else 0,
            retrieval_time_ms=retrieval_time_ms
        )
        
        # Return empty list if no data (not None) - let check_context handle fallback
        return {
            "retrieved_context": data if data else [],
            "source_type": "lms"
        }
        
    except Exception as e:
        logger.error(f"Error fetching LMS: {e}", exc_info=True)
        # Persist error context
        try:
            context_repo = RetrievedContextRepo()
            admin_id = state.get("admin_id", "anonymous")
            query = state.get("user_message", "")
            context_repo.save_context(
                session_id=state.get("session_id", "unknown"),
                admin_id=admin_id,
                source_type="lms",
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
            "source_type": "lms"
        }
