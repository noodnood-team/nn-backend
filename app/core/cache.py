"""Thin Redis caching layer.

* Connects/disconnects via the FastAPI lifespan (``init_cache`` / ``close_cache``).
* Provides ``cache_get``, ``cache_set``, ``cache_delete``, and
  ``invalidate_prefix`` helpers that silently degrade when Redis is
  unreachable so the API never crashes because of the cache.
* Exposes ``get_redis`` as a FastAPI dependency for route-level usage.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)

_pool: redis.Redis | None = None

# Default TTLs (seconds) – importers can override per-call.
DEFAULT_TTL = 60  # 1 minute
SUMMARY_TTL = 30  # dashboard summary – short because new scans change it
RECORD_TTL = 300  # individual record lookup – records are immutable
PREDICT_TTL = 300  # same-image prediction dedup – 5 minutes


async def init_cache(redis_url: str) -> None:
    """Create the global Redis connection pool."""
    global _pool
    try:
        _pool = redis.from_url(redis_url, decode_responses=True)
        await _pool.ping()
        logger.info("Redis cache connected (%s)", redis_url)
    except Exception:
        logger.warning("Redis unavailable – caching disabled", exc_info=True)
        _pool = None


async def close_cache() -> None:
    """Gracefully shut down the pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        logger.info("Redis cache connection closed")


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

async def cache_get(key: str) -> Any | None:
    """Return deserialised value or ``None`` on miss / error."""
    if _pool is None:
        return None
    try:
        raw = await _pool.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.debug("cache_get failed for key=%s", key, exc_info=True)
        return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Serialise *value* to JSON and store with an expiry."""
    if _pool is None:
        return
    try:
        await _pool.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.debug("cache_set failed for key=%s", key, exc_info=True)


async def cache_delete(key: str) -> None:
    if _pool is None:
        return
    try:
        await _pool.delete(key)
    except Exception:
        logger.debug("cache_delete failed for key=%s", key, exc_info=True)


async def invalidate_prefix(prefix: str) -> int:
    """Delete every key that starts with *prefix*. Returns count deleted."""
    if _pool is None:
        return 0
    deleted = 0
    try:
        async for key in _pool.scan_iter(match=f"{prefix}*", count=200):
            await _pool.delete(key)
            deleted += 1
    except Exception:
        logger.debug("invalidate_prefix failed for %s", prefix, exc_info=True)
    return deleted


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_redis() -> redis.Redis | None:
    """Inject the pool into a route; may be ``None``."""
    return _pool
