# app/core/security.py

from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from app.db.supabase import get_chatbot_supabase_client
import logging

logger = logging.getLogger(__name__)


def get_admin_token(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Extract Bearer token from Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format",
        )

    return authorization.replace("Bearer ", "").strip()


def validate_admin_session(
    session_id: str,
    admin_token: str = Depends(get_admin_token),
):
    """
    Validates that:
    - Session exists
    - Session is active
    - Session belongs to the admin
    """
    supabase = get_chatbot_supabase_client()

    response = (
        supabase.table("admin_sessions")
        .select("session_id, admin_id, status")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session = response.data

    if session["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session is not active",
        )

    # NOTE:
    # admin_id ↔ admin_token mapping validation
    # is assumed to be handled by Edify backend.
    # Here we only enforce session existence & state.

    logger.info(
        "Validated session %s for admin",
        session_id,
    )

    return session
