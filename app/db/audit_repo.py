from typing import Dict, Any, Optional
from app.db.supabase import get_chatbot_supabase_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AuditRepo:
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.table = "audit_logs"

    def log_action(self, admin_id: str, action: str, details: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> bool:
        """
        Logs an admin action. Append-only.
        Handles UUID conversion for admin_id.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import uuid
            
            # Convert admin_id to UUID if needed
            if admin_id == "anonymous" or not admin_id:
                admin_uuid = "00000000-0000-0000-0000-000000000000"
            else:
                try:
                    admin_uuid = str(uuid.UUID(admin_id))
                except ValueError:
                    admin_uuid = "00000000-0000-0000-0000-000000000000"
            
            data = {
                "admin_id": admin_uuid,
                "action": action,
                "metadata": details or {},  # Schema uses 'metadata', not 'details'
            }
            if session_id:
                data["session_id"] = session_id
            
            result = self.supabase.table(self.table).insert(data).execute()
            
            if result.data:
                logger.debug(f"Audit logged: {action} for admin {admin_uuid}")
                return True
            else:
                logger.error(f"Failed to log audit action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging audit action: {e}", exc_info=True)
            # Audit failure shouldn't crash the app, but should be noted.
            return False
