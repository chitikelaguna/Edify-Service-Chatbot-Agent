from typing import Any, List, Dict
from app.db.supabase import get_edify_supabase_client
import logging

logger = logging.getLogger(__name__)

class RMSRepo:
    """
    Repository for RMS data access.
    Reads from Edify RMS tables using Edify Supabase client (read-only).
    Contains NO business logic - only data retrieval.
    """
    
    def __init__(self):
        self.supabase = get_edify_supabase_client()
        self.table = "rms_candidates"

    def search_rms(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches RMS candidates data.
        Returns raw verified data from Supabase.
        
        Args:
            query: Search query string
            
        Returns:
            List of RMS candidate records (raw data from Supabase)
        """
        try:
            # Use Supabase ilike for case-insensitive text search
            # Search across common RMS fields
            response = (
                self.supabase.table(self.table)
                .select("*")
                .or_(f"name.ilike.%{query}%,skills.ilike.%{query}%,role.ilike.%{query}%,status.ilike.%{query}%,position.ilike.%{query}%")
                .limit(10)
                .execute()
            )
            
            logger.info(f"Retrieved {len(response.data)} RMS records")
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching RMS: {e}", exc_info=True)
            return []
