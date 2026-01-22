from app.db.supabase import get_chatbot_supabase_client
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.table = "admin_sessions"

    def create_session(self, admin_id: str) -> Dict[str, Any]:
        """
        Creates a new active session for the admin.
        Handles UUID conversion for admin_id.
        """
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
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
                "status": "active",
                "created_at": now,
                "last_activity": now  # Schema uses 'last_activity', not 'updated_at'
            }
            
            # Insert into Supabase
            result = self.supabase.table(self.table).insert(data).execute()
            
            if result.data:
                logger.info(f"Created session {session_id} for admin {admin_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create session record")
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise e

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        Ends an existing session.
        """
        try:
            now = datetime.utcnow().isoformat()
            
            data = {
                "status": "ended",
                "ended_at": now,
                "last_activity": now  # Schema uses 'last_activity', not 'updated_at'
            }
            
            # Update Supabase
            result = (
                self.supabase.table(self.table)
                .update(data)
                .eq("session_id", session_id)
                .execute()
            )
            
            if result.data:
                logger.info(f"Ended session {session_id}")
                return result.data[0]
            else:
                # If no raw returned, it might check if session exists first, 
                # but update should return data if successful and rows matched.
                raise Exception("Session not found or upgrade failed")
                
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            raise e

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves session details.
        """
        try:
            result = (
                self.supabase.table(self.table)
                .select("*")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return None
    
    def update_last_activity(self, session_id: str) -> bool:
        """
        Updates the last_activity timestamp for a session.
        Should be called on every user interaction.
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            result = (
                self.supabase.table(self.table)
                .update({"last_activity": now})
                .eq("session_id", session_id)
                .execute()
            )
            
            if result.data:
                return True
            else:
                logger.warning(f"Failed to update last_activity for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating last_activity: {e}", exc_info=True)
            return False
