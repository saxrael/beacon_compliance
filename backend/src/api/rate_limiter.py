"""Rate Limiting Middleware for Beacon Compliance (rate_limiter.py).

Implements IP-based token bucket rate limiting for FastAPI endpoints.
Enforces strict rate limits on sensitive endpoints (e.g. sign-off approval)
and standard limits on general API routes.
"""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False
    RateLimitExceeded = Exception
    _rate_limit_exceeded_handler = None


def get_real_client_ip(request: Request) -> str:
    """Extract real client IP handling Cloudflare, Caddy, and reverse proxy headers."""
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


limiter = (
    Limiter(key_func=get_real_client_ip, default_limits=["100/minute"]) if HAS_SLOWAPI else None
)


class SlidingWindowLimiter:
    """Sliding window rate limiter with multi-key IP tracking."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(
        self, client_ip: str, limit_override: int | None = None
    ) -> tuple[bool, int, int]:
        now = time.time()
        limit = limit_override or self.requests_per_minute
        cutoff = now - self.window_seconds

        timestamps = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = timestamps

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            reset_in = int(self.window_seconds - (now - oldest)) + 1
            return False, 0, max(reset_in, 1)

        timestamps.append(now)
        remaining = limit - len(timestamps)
        return True, remaining, self.window_seconds


standard_limiter = SlidingWindowLimiter(requests_per_minute=100)
strict_signoff_limiter = SlidingWindowLimiter(requests_per_minute=10)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware enforcing IP-based sliding window rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_real_client_ip(request)
        path = request.url.path

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
            return Response(
                content=f'{{"detail":"Rate limit exceeded. Please try again in {reset_in } seconds."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(10 if path.startswith("/api/signoff") else 100),
                    "X-RateLimit-Remaining": "0",
                    "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                    "Access-Control-Allow-Credentials": "true",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(10 if path.startswith("/api/signoff") else 100)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
