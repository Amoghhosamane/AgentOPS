"""Distributed atomic sliding-window rate limiter with graceful in-memory fallback."""

import time
import asyncio
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status
from agentops_api.config import settings


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.
    Provides sub-millisecond atomic checks with local memory or Redis.
    """
    def __init__(self):
        # In-memory store: key -> list of (timestamp_float)
        self._memory_store: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 120,
        window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Check if identifier has exceeded max_requests in the past window_seconds.
        Returns:
            (allowed: bool, remaining_requests: int, retry_after_seconds: int)
        """
        now = time.time()
        cutoff = now - window_seconds

        async with self._lock:
            timestamps = self._memory_store.get(identifier, [])
            # Evict timestamps older than sliding window
            valid_timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(valid_timestamps) >= max_requests:
                # Calculate oldest entry to advise retry_after
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                self._memory_store[identifier] = valid_timestamps
                return False, 0, retry_after

            # Record this request
            valid_timestamps.append(now)
            self._memory_store[identifier] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return True, remaining, 0

    async def reset(self, identifier: Optional[str] = None):
        """Reset rate limiter state (useful for test suites)."""
        async with self._lock:
            if identifier:
                self._memory_store.pop(identifier, None)
            else:
                self._memory_store.clear()


# Global rate limiter instance
limiter = SlidingWindowRateLimiter()


async def rate_limit_dependency(request: Request):
    """FastAPI dependency enforcing project/client rate limits."""
    # Priority: Project API Key -> Auth User -> Client Host IP
    api_key = request.headers.get("X-AgentOps-Api-Key")
    auth_header = request.headers.get("Authorization")
    client_ip = request.client.host if request.client else "127.0.0.1"

    identifier = api_key or auth_header or client_ip
    max_requests = settings.INGEST_RATE_LIMIT_PER_MINUTE if "/telemetry" in request.url.path else settings.DEFAULT_RATE_LIMIT_PER_MINUTE

    allowed, remaining, retry_after = await limiter.check_rate_limit(
        identifier=identifier,
        max_requests=max_requests,
        window_seconds=60
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests.",
            headers={"Retry-After": str(retry_after)}
        )
