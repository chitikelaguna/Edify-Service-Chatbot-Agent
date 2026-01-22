from typing import List, Dict, Optional
from app.db.supabase import get_chatbot_supabase_client
import logging
import uuid

logger = logging.getLogger(__name__)

class ChatHistoryRepo:
    """
    Repository for chat_history table.
    Stores user messages and assistant responses together with metadata.
    """
    
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.table = "chat_history"
    
    def save_chat_history(
        self,
        session_id: str,
        admin_id: str,
        user_message: str,
        assistant_response: str,
        source_type: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None
    ) -> bool:
        """
        Saves a chat history entry (user message + assistant response pair).
        
        Args:
            session_id: Session UUID
            admin_id: Admin/user ID (will be converted to UUID if needed)
            user_message: User's message
            assistant_response: Assistant's response
            source_type: Optional source type ('crm', 'lms', 'rms', 'rag', 'none')
            response_time_ms: Optional response time in milliseconds
            tokens_used: Optional number of tokens used
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert admin_id to UUID if it's not already
            # Handle "anonymous" or other string IDs
            if admin_id == "anonymous" or not admin_id:
                # Use a fixed UUID for anonymous users
                admin_uuid = "00000000-0000-0000-0000-000000000000"
            else:
                try:
                    # Try to parse as UUID
                    admin_uuid = str(uuid.UUID(admin_id))
                except ValueError:
                    # If not a valid UUID, use anonymous UUID
                    admin_uuid = "00000000-0000-0000-0000-000000000000"
            
            data = {
                "session_id": session_id,
                "admin_id": admin_uuid,
                "user_message": user_message,
                "assistant_response": assistant_response,
            }
            
            if source_type:
                data["source_type"] = source_type
            
            if response_time_ms is not None:
                data["response_time_ms"] = response_time_ms
            
            if tokens_used is not None:
                data["tokens_used"] = tokens_used
            
            result = self.supabase.table(self.table).insert(data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Successfully saved chat history for session {session_id[:8]}... (id: {result.data[0].get('id')})")
                return True
            else:
                logger.error(f"Failed to save chat history - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error saving chat history: {e}", exc_info=True)
            # Log more details about the error
            if hasattr(e, 'args') and len(e.args) > 0:
                error_details = e.args[0]
                if isinstance(error_details, dict):
                    logger.error(f"Error details: {error_details}")
            return False
    
    def get_chat_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """
        Retrieves chat history for a session.
        
        Args:
            session_id: Session UUID
            limit: Maximum number of records to return
            
        Returns:
            List of chat history records
        """
        try:
            response = (
                self.supabase.table(self.table)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}", exc_info=True)
            return []
    
    def get_chat_history_by_admin(
        self,
        admin_id: str,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """
        Retrieves chat history for an admin/user.
        
        Args:
            admin_id: Admin/user ID
            limit: Maximum number of records to return
            
        Returns:
            List of chat history records
        """
        try:
            response = (
                self.supabase.table(self.table)
                .select("*")
                .eq("admin_id", admin_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching chat history by admin: {e}", exc_info=True)
            return []

