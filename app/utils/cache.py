"""
Optional caching utilities using Redis.
Only active if ENABLE_CACHING is True in settings.
Non-breaking: Falls back gracefully if Redis is unavailable.
"""
from typing import Any, Optional
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

# Global Redis client (initialized only if caching is enabled)
_redis_client = None

def get_redis_client():
    """Get Redis client (lazy initialization, only if caching enabled)."""
    global _redis_client
    
    if not settings.ENABLE_CACHING:
        return None
    
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=2,  # Fast fail if Redis unavailable
                socket_timeout=2
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis caching enabled and connected")
        except ImportError:
            logger.warning("redis package not installed - caching disabled. Install with: pip install redis")
            return None
        except Exception as e:
            logger.warning(f"Redis connection failed - caching disabled: {e}")
            return None
    
    return _redis_client

def get_cached(key: str) -> Optional[Any]:
    """
    Get value from cache (if caching enabled).
    Returns None if not found or caching disabled.
    Non-breaking: Always returns None if caching unavailable.
    """
    if not settings.ENABLE_CACHING:
        return None
    
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.debug(f"Cache get failed for key {key}: {e}")
    
    return None

def set_cached(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Set value in cache (if caching enabled).
    Returns True if successful, False otherwise.
    Non-breaking: Silently fails if caching unavailable.
    """
    if not settings.ENABLE_CACHING:
        return False
    
    client = get_redis_client()
    if not client:
        return False
    
    try:
        ttl = ttl or settings.CACHE_TTL_SECONDS
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.debug(f"Cache set failed for key {key}: {e}")
        return False

def delete_cached(key: str) -> bool:
    """
    Delete value from cache (if caching enabled).
    Returns True if successful, False otherwise.
    Non-breaking: Silently fails if caching unavailable.
    """
    if not settings.ENABLE_CACHING:
        return False
    
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.debug(f"Cache delete failed for key {key}: {e}")
        return False

def cache_key_chat_history(session_id: str) -> str:
    """Generate cache key for chat history."""
    return f"chat_history:{session_id}"

def cache_key_crm_query(query: str, table: str) -> str:
    """Generate cache key for CRM query."""
    import hashlib
    query_hash = hashlib.md5(f"{query}:{table}".encode()).hexdigest()
    return f"crm_query:{table}:{query_hash}"

