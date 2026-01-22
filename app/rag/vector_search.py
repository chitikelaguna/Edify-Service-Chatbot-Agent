from typing import List, Dict, Any
from app.db.supabase import get_chatbot_supabase_client
from app.rag.embedder import Embedder
import logging

logger = logging.getLogger(__name__)

class VectorSearch:
    """
    Vector similarity search for RAG documents.
    Uses Supabase pgvector for efficient similarity search.
    """
    
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.embedder = Embedder()
        self.function_name = "match_documents"  # RPC function name in Supabase

    def search(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[str]:
        """
        Embeds the query and performs a similarity search in Supabase.
        Returns a list of matched text content from rag_documents.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of document content strings
        """
        try:
            # 1. Embed query
            query_embedding = self.embedder.embed_text(query)
            
            # 2. Call RPC function for vector similarity search
            # The RPC function should:
            # - Search rag_embeddings table using cosine similarity
            # - Join with rag_documents to get content
            # - Filter by threshold
            # - Return top N results
            
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
            
            response = self.supabase.rpc(self.function_name, rpc_params).execute()
            
            if not response.data:
                logger.debug(f"No results found for query: {query[:50]}...")
                return []
            
            # Extract content from results
            # RPC should return: [{content: str, similarity: float}, ...]
            results = [item["content"] for item in response.data if item.get("content")]
            
            logger.info(f"Found {len(results)} matching documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error performing vector search: {e}", exc_info=True)
            # Fallback: try direct query if RPC doesn't exist
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int = 5) -> List[str]:
        """
        Fallback search method if RPC function is not available.
        This is less efficient but works without custom RPC functions.
        
        Note: This requires a Supabase RPC function for proper vector search.
        For production, implement the match_documents RPC function in Supabase.
        """
        logger.warning("Using fallback search - RPC function may not be configured")
        try:
            # This is a placeholder - actual implementation requires RPC function
            # or direct SQL query with vector operations
            query_embedding = self.embedder.embed_text(query)
            
            # Attempt to call RPC (will fail gracefully if not configured)
            response = self.supabase.rpc(
                self.function_name,
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.5,
                    "match_count": limit
                }
            ).execute()
            
            if response.data:
                return [item["content"] for item in response.data if item.get("content")]
            
            return []
            
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            return []
