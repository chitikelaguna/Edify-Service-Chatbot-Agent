from typing import Any, List, Dict
from app.db.supabase import get_edify_supabase_client
import logging

logger = logging.getLogger(__name__)

class LMSRepo:
    """
    Repository for LMS data access.
    Reads from Edify LMS tables using Edify Supabase client (read-only).
    Contains NO business logic - only data retrieval.
    """
    
    def __init__(self):
        self.supabase = get_edify_supabase_client()
        self.table = "lms_batches"

    def search_lms(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches LMS batches data.
        Returns raw verified data from Supabase.
        
        Args:
            query: Search query string
            
        Returns:
            List of LMS batch records (raw data from Supabase)
        """
        try:
            # Use Supabase ilike for case-insensitive text search
            # Search across common LMS fields
            response = (
                self.supabase.table(self.table)
                .select("*")
                .or_(f"name.ilike.%{query}%,title.ilike.%{query}%,description.ilike.%{query}%,instructor.ilike.%{query}%,course_name.ilike.%{query}%")
                .limit(10)
                .execute()
            )
            
            logger.info(f"Retrieved {len(response.data)} LMS records")
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching LMS: {e}", exc_info=True)
            return []
