# app/db/supabase.py

from supabase import create_client, Client
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Optional: Connection pool configuration (if enabled)
def _get_client_options():
    """Get optional client options for connection pooling."""
    if settings.ENABLE_CONNECTION_POOLING:
        try:
            from supabase.client import ClientOptions
            return ClientOptions(
                # Note: Supabase Python client uses httpx internally
                # Connection pooling is handled by httpx connection pool
                # These options are passed through if supported
            )
        except ImportError:
            logger.debug("ClientOptions not available in this supabase version")
    return None

# Separate clients for Edify (read-only) and Chatbot (read/write)
_edify_supabase_client: Client | None = None
_chatbot_supabase_client: Client | None = None


def _ensure_no_proxy_env():
    """
    Temporarily remove proxy environment variables to prevent gotrue proxy errors.
    gotrue 2.8.1 may incorrectly handle proxy parameters.
    """
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    saved = {}
    for var in proxy_vars:
        if var in os.environ:
            saved[var] = os.environ.pop(var)
    return saved


def _restore_proxy_env(saved: dict):
    """Restore proxy environment variables."""
    os.environ.update(saved)


def get_edify_supabase_client() -> Client:
    """
    Returns a singleton Supabase client for Edify Production database.
    READ-ONLY access only - used for CRM, LMS, RMS data retrieval.
    Uses service_role key (backend-only).
    """
    global _edify_supabase_client

    if _edify_supabase_client is None:
        logger.info("Initializing Edify Supabase client (read-only)")
        # Temporarily remove proxy env vars to prevent gotrue errors
        saved_proxy = _ensure_no_proxy_env()
        try:
            _edify_supabase_client = create_client(
                settings.EDIFY_SUPABASE_URL,
                settings.EDIFY_SUPABASE_SERVICE_ROLE_KEY
            )
        finally:
            _restore_proxy_env(saved_proxy)

    return _edify_supabase_client


def get_chatbot_supabase_client() -> Client:
    """
    Returns a singleton Supabase client for Chatbot database.
    READ/WRITE access - used for sessions, memory, RAG, audit logs.
    Uses service_role key (backend-only).
    """
    global _chatbot_supabase_client

    if _chatbot_supabase_client is None:
        logger.info("Initializing Chatbot Supabase client (read/write)")
        # Temporarily remove proxy env vars to prevent gotrue errors
        saved_proxy = _ensure_no_proxy_env()
        try:
            _chatbot_supabase_client = create_client(
                settings.CHATBOT_SUPABASE_URL,
                settings.CHATBOT_SUPABASE_SERVICE_ROLE_KEY
            )
        finally:
            _restore_proxy_env(saved_proxy)

    return _chatbot_supabase_client


# Backward compatibility alias - defaults to Chatbot client
# This can be used by existing code that doesn't specify which client
def get_supabase_client() -> Client:
    """
    Returns Chatbot Supabase client (backward compatibility).
    For new code, use get_chatbot_supabase_client() or get_edify_supabase_client() explicitly.
    """
    return get_chatbot_supabase_client()
