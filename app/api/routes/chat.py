from fastapi import APIRouter, HTTPException, Depends, status, Header, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.security import get_admin_token
from app.core.config import settings
from app.services.chat_service import ChatService
from app.db.supabase import get_chatbot_supabase_client
import logging
import uuid

# Define Router
router = APIRouter()
logger = logging.getLogger(__name__)

# Optional rate limiting decorator
# Applied only if ENABLE_RATE_LIMITING=true and slowapi is installed
def apply_rate_limit(func):
    """Apply rate limiting decorator if enabled."""
    if settings.ENABLE_RATE_LIMITING:
        try:
            # Import here to avoid errors if slowapi not installed
            from slowapi import Limiter
            from slowapi.util import get_remote_address
            limiter = Limiter(key_func=get_remote_address)
            return limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")(func)
        except ImportError:
            pass
    return func

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """
    Gets existing session or creates a new one if it doesn't exist.
    No authentication required.
    """
    supabase = get_chatbot_supabase_client()
    
    # Try to get existing session (only if it's not a temp session)
    if not session_id.startswith('temp-'):
        try:
            response = (
                supabase.table("admin_sessions")
                .select("session_id, admin_id, status")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            
            if response.data and response.data["status"] == "active":
                return response.data
        except Exception as e:
            logger.warning(f"Session lookup failed: {e}, creating new session")
    
    # Session doesn't exist or is inactive, create new one
    from app.services.session_service import SessionService
    service = SessionService()
    session_data = service.create_session("anonymous")
    return session_data

@router.post("/message", response_model=ChatResponse)
@apply_rate_limit
async def chat_message(
    request: ChatRequest
):
    """
    Chat message endpoint with full persistence.
    All data is persisted to database including errors.
    
    Optional rate limiting is applied if ENABLE_RATE_LIMITING=true.
    """
    try:
        # Get or create session (no auth required)
        session_data = get_or_create_session(request.session_id)
        
        # Use the actual session_id from the created/retrieved session
        actual_session_id = session_data["session_id"]
        
        service = ChatService()
        response_text = await service.process_user_message(
            session_id=actual_session_id,
            user_message=request.message,
            session_data=session_data
        )
        
        return ChatResponse(response=response_text, session_id=actual_session_id)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        # Audit log endpoint error
        try:
            from app.db.audit_repo import AuditRepo
            audit = AuditRepo()
            audit.log_action(
                admin_id=session_data.get("admin_id", "unknown") if 'session_data' in locals() else "unknown",
                action="chat_endpoint_error",
                details={"error": str(e), "message": request.message[:100]},
                session_id=session_data.get("session_id") if 'session_data' in locals() else None
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))
