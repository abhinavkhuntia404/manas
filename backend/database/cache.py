"""
Upstash Redis & Standard Redis caching client for MANAS.
Supports both Upstash REST API and standard Redis connection string (rediss://...).
Gracefully falls back to direct execution when Redis is not configured.
"""

import json
import logging
from typing import Optional, Any
from functools import wraps

from configs.settings import get_settings

logger = logging.getLogger("manas.cache")
settings = get_settings()

_redis_client = None
_redis_initialized = False


def get_redis_client():
    global _redis_client, _redis_initialized
    if _redis_initialized:
        return _redis_client

    _redis_initialized = True
    
    # 1. Try Upstash REST URL + Token
    upstash_url = getattr(settings, "upstash_redis_rest_url", None) or None
    upstash_token = getattr(settings, "upstash_redis_rest_token", None) or None
    
    # 2. Or standard Redis connection URI (e.g., rediss://...)
    redis_url = getattr(settings, "redis_url", None) or None

    try:
        if upstash_url and upstash_token:
            from upstash_redis import Redis
            _redis_client = Redis(url=upstash_url, token=upstash_token)
            logger.info("Connected to Upstash Redis via REST API.")
        elif redis_url:
            import redis
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Connected to Redis server.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis/Upstash: {e}. Running without cache.")
        _redis_client = None

    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    client = get_redis_client()
    if not client:
        return None
    try:
        val = client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.debug(f"Cache get failed for {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    client = get_redis_client()
    if not client:
        return False
    try:
        serialized = json.dumps(value, default=str)
        client.set(key, serialized, ex=ttl_seconds)
        return True
    except Exception as e:
        logger.debug(f"Cache set failed for {key}: {e}")
        return False
