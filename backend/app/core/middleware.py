from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitError
from app.core.rate_limit import rate_limiter

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


# Endpoints never worth throttling: CORS preflight carries no real load,
# and health checks are typically polled frequently by infra/uptime tools.
_RATE_LIMIT_EXEMPT_PATHS = {"/api/health"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client-IP sliding-window throttle across the whole API. Runs
    ahead of routing, so it applies uniformly without touching any
    individual route. Raised here (rather than via the app's normal
    AppError exception handler) because middleware added through
    add_middleware sits outside Starlette's built-in ExceptionMiddleware
    -- an exception raised here wouldn't reach that handler."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS" or request.url.path in _RATE_LIMIT_EXEMPT_PATHS:
            return await call_next(request)

        client_key = request.client.host if request.client else "unknown"
        try:
            rate_limiter.check(client_key)
        except RateLimitError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.message},
                headers={"Retry-After": str(rate_limiter.window_seconds)},
            )

        return await call_next(request)
