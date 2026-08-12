"""Rate Limiting Middleware for Beacon Compliance (rate_limiter.py).

Implements IP-based token bucket rate limiting for FastAPI endpoints.
Enforces strict rate limits on sensitive endpoints (e.g. sign-off approval)
and standard limits on general API routes.
"""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(
        self, client_ip: str, limit_override: int | None = None
    ) -> tuple[bool, int, int]:
        """Check if request from client_ip is allowed under the rate limit.

        Returns (allowed, remaining, reset_seconds).
        """
        now = time.time()
        limit = limit_override or self.requests_per_minute
        cutoff = now - self.window_seconds

        # Prune timestamps older than window
        timestamps = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = timestamps

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            reset_in = int(self.window_seconds - (now - oldest)) + 1
            return False, 0, max(reset_in, 1)

        timestamps.append(now)
        remaining = limit - len(timestamps)
        return True, remaining, self.window_seconds


# Global rate limiter instances
standard_limiter = RateLimiter(requests_per_minute=100)
strict_signoff_limiter = RateLimiter(requests_per_minute=10)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware enforcing IP-based sliding window rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path

        # Apply strict limit on sign-off approval endpoint
        if path.startswith("/api/signoff"):
            allowed, remaining, reset_in = strict_signoff_limiter.is_allowed(
                client_ip, limit_override=10
            )
        elif path.startswith("/api/"):
            allowed, remaining, reset_in = standard_limiter.is_allowed(
                client_ip, limit_override=100
            )
        else:
            allowed, remaining, reset_in = True, 100, 60

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again in {reset_in} seconds.",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": "10",
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(
            100 if not path.startswith("/api/signoff") else 10
        )
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
