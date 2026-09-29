from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.exceptions import RateLimitError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import decode_token

_settings = get_settings()

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Applies to every response, API and static alike. The Cache-Control
    addition below exists specifically because of a real incident: a
    browser cached a 403 response from a permission-gated endpoint (no
    server-issued cache header at all meant the browser fell back to its
    own heuristic caching for a GET request), and kept silently
    replaying that stale failure indefinitely -- surviving password
    changes, role changes, and even full backend restarts, since none of
    those touch anything the browser was actually checking. Every /api/
    response now explicitly forbids caching, so this can't recur for any
    endpoint, successful or not. Static assets (the built frontend) are
    deliberately left alone -- those *should* cache, and already carry
    their own appropriate headers from how they're served."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


# Endpoints never worth throttling: CORS preflight carries no real load,
# and health checks are typically polled frequently by infra/uptime tools.
_RATE_LIMIT_EXEMPT_PATHS = {"/api/health"}


_user_rate_limiter = SlidingWindowRateLimiter(_settings.RATE_LIMIT_PER_USER, _settings.RATE_LIMIT_WINDOW_SECONDS)
_ip_rate_limiter = SlidingWindowRateLimiter(_settings.RATE_LIMIT_PER_IP, _settings.RATE_LIMIT_WINDOW_SECONDS)


def client_ip(request: Request) -> str:
    """The caller's real IP. X-Forwarded-For is only honoured when the
    direct peer is a trusted proxy on this host (the Vite dev proxy, or
    nginx) -- otherwise anyone could send a fresh fake value per request.
    The rightmost entry is the one our own proxy appended, so it can't be
    forged by the client either."""
    peer = request.client.host if request.client else "unknown"
    if peer in _settings.trusted_proxy_ips:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            last = forwarded.rsplit(",", 1)[-1].strip()
            if last:
                return last
    return peer


def _rate_limit_bucket(request: Request) -> tuple[SlidingWindowRateLimiter, str]:
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() == "bearer ":
        try:
            payload = decode_token(auth[7:].strip())
        except ValueError:
            payload = None
        # Only a validly signed access token earns a per-user bucket; a
        # garbage/expired token falls back to the IP bucket so it can't
        # be used to mint unlimited fresh buckets.
        if payload and payload.get("type") == "access":
            return _user_rate_limiter, f"user:{payload['sub']}"
    return _ip_rate_limiter, f"ip:{client_ip(request)}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window throttle across the whole API: per signed-in user,
    or per client IP for anonymous calls (see RATE_LIMIT_PER_USER in
    config.py for why not per IP alone). Runs ahead of routing, so it
    applies uniformly without touching any individual route. Raised here
    (rather than via the app's normal AppError exception handler) because
    middleware added through add_middleware sits outside Starlette's
    built-in ExceptionMiddleware -- an exception raised here wouldn't
    reach that handler."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS" or not request.url.path.startswith("/api/") or request.url.path in _RATE_LIMIT_EXEMPT_PATHS:
            return await call_next(request)

        limiter, key = _rate_limit_bucket(request)
        try:
            limiter.check(key)
        except RateLimitError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.message},
                headers={"Retry-After": str(limiter.window_seconds)},
            )

        return await call_next(request)
