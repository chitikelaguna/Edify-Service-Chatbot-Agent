from typing import Dict, Any
from app.langgraph.state import AgentState
from app.rag.vector_search import VectorSearch
from app.db.retrieved_context_repo import RetrievedContextRepo
import logging

logger = logging.getLogger(__name__)

def fetch_rag_node(state: AgentState) -> Dict[str, Any]:
    """
    Fetches RAG data from vector search and attaches to state.
    Persists retrieved data to database.
    """
    try:
        query = state["user_message"]
        session_id = state["session_id"]
        search_engine = VectorSearch()
        
        import time
        retrieval_start = time.time()
        # Search for documents
        documents = search_engine.search(query, limit=3)
        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
        
        # Persist retrieved context to database
        context_repo = RetrievedContextRepo()
        admin_id = state.get("admin_id", "anonymous")
        context_repo.save_context(
            session_id=session_id,
            admin_id=admin_id,
            source_type="rag",
            query_text=query,
            payload={"data": documents if documents else []},  # Only store retrieved data, not query
            record_count=len(documents) if documents else 0,
            retrieval_time_ms=retrieval_time_ms
        )
        
        return {
            "retrieved_context": documents if documents else [],
            "source_type": "rag"
        }
        
    except Exception as e:
        logger.error(f"Error fetching RAG: {e}", exc_info=True)
        # Persist error context
        try:
            context_repo = RetrievedContextRepo()
            admin_id = state.get("admin_id", "anonymous")
            query = state.get("user_message", "")
            context_repo.save_context(
                session_id=state.get("session_id", "unknown"),
                admin_id=admin_id,
                source_type="rag",
                query_text=query,
                payload={"error": str(e)},  # Only store error, query is in query_text column
                record_count=0,
                error_message=str(e)
            )
        except:
            pass
        return {
            "retrieved_context": [],
            "source_type": "rag"
        }
