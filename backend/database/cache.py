"""
Upstash Redis & Standard Redis caching client for MANAS.
Supports native Upstash REST API and standard Redis connection string (rediss://...).
Gracefully falls back to direct database execution when Redis is not configured.
"""

import json
import logging
import requests
from typing import Optional, Any

from configs.settings import get_settings

logger = logging.getLogger("manas.cache")
settings = get_settings()

_redis_client = None
_is_upstash_rest = False
_upstash_url = None
_upstash_headers = None
_initialized = False


def _init_client():
    global _redis_client, _is_upstash_rest, _upstash_url, _upstash_headers, _initialized
    if _initialized:
        return

    _initialized = True

    upstash_url = getattr(settings, "upstash_redis_rest_url", None)
    upstash_token = getattr(settings, "upstash_redis_rest_token", None)
    redis_url = getattr(settings, "redis_url", None)

    if upstash_url and upstash_token:
        _is_upstash_rest = True
        _upstash_url = upstash_url.rstrip("/")
        _upstash_headers = {
            "Authorization": f"Bearer {upstash_token}",
            "Content-Type": "application/json",
        }
        logger.info(f"Connected to Upstash Redis REST API at {_upstash_url}")
    elif redis_url:
        try:
            import redis
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Connected to Redis server via URI.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")


def cache_get(key: str) -> Optional[Any]:
    """Retrieve JSON-deserialized object from cache."""
    _init_client()
    if _is_upstash_rest:
        try:
            res = requests.get(
                f"{_upstash_url}/get/{key}",
                headers=_upstash_headers,
                timeout=3,
            )
            if res.status_code == 200:
                data = res.json().get("result")
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.debug(f"Upstash GET failed for {key}: {e}")
        return None

    if _redis_client:
        try:
            val = _redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.debug(f"Redis GET failed for {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """Store JSON-serializable object into cache with TTL."""
    _init_client()
    try:
        serialized = json.dumps(value, default=str)
    except Exception as e:
        logger.debug(f"Serialization failed for {key}: {e}")
        return False

    if _is_upstash_rest:
        try:
            res = requests.post(
                f"{_upstash_url}/set/{key}?ex={ttl_seconds}",
                data=serialized,
                headers=_upstash_headers,
                timeout=3,
            )
            return res.status_code == 200
        except Exception as e:
            logger.debug(f"Upstash SET failed for {key}: {e}")
            return False

    if _redis_client:
        try:
            _redis_client.set(key, serialized, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.debug(f"Redis SET failed for {key}: {e}")
    return False
