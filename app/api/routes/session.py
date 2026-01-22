from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.session_service import SessionService
from app.core.security import get_admin_token
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class StartSessionRequest(BaseModel):
    admin_id: Optional[str] = "anonymous"

class StartSessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: str

class EndSessionRequest(BaseModel):
    session_id: str

class EndSessionResponse(BaseModel):
    session_id: str
    status: str
    ended_at: Optional[str] = None

@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    request: Optional[StartSessionRequest] = None
):
    """
    Start a new session. Admin ID is optional - defaults to 'anonymous' if not provided.
    No authentication required.
    """
    try:
        service = SessionService()
        admin_id = request.admin_id if request else "anonymous"
        session_data = service.create_session(admin_id)
        
        return StartSessionResponse(
            session_id=session_data["session_id"],
            status=session_data["status"],
            created_at=session_data["created_at"]
        )
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Could not start session"
        )

@router.post("/start-anonymous", response_model=StartSessionResponse)
async def start_anonymous_session():
    """
    Start an anonymous session without any authentication.
    """
    try:
        service = SessionService()
        session_data = service.create_session("anonymous")
        
        return StartSessionResponse(
            session_id=session_data["session_id"],
            status=session_data["status"],
            created_at=session_data["created_at"]
        )
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Could not start session"
        )

@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    request: EndSessionRequest
):
    try:
        service = SessionService()
        # Verify session existence/ownership could happen here or in service.
        # For valid end, we just declare it ended.
        
        session_data = service.end_session(request.session_id)
        
        return EndSessionResponse(
            session_id=session_data["session_id"],
            status=session_data["status"],
            ended_at=session_data.get("ended_at")
        )
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not end session"
        )
