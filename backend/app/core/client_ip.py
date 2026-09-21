from fastapi import Request

from app.core.config import get_settings


def get_client_ip(request: Request) -> str:
    """The caller's real IP, for rate-limiting and login-lockout keys
    (auth_service.py's per-IP lockout, core/middleware.py's
    RateLimitMiddleware).

    Defaults to the raw TCP peer address (request.client.host) -- correct
    for this app's documented default deployment: a single process, hit
    directly, no reverse proxy in front. X-Forwarded-For is never trusted
    at the default TRUSTED_PROXY_COUNT=0: it's just a request header, so
    any client can set it to anything, including someone else's IP, and
    blindly trusting it would let one attacker either dodge the per-IP
    login lockout/rate limit entirely (claim a fresh IP on every request)
    or frame another IP for their own attempts.

    Set TRUSTED_PROXY_COUNT (app/core/config.py) to the number of reverse
    proxies actually deployed in front of this app (usually 1) to opt in.
    With N trusted hops, each of those proxies appends the address it saw
    the request come from as it forwards X-Forwarded-For, so the value N
    entries from the *right* end of that header is the one your own
    trusted proxy chain appended -- not whatever a client put at the
    front of it -- and so can't be spoofed by the request's actual
    sender. Entries to the left of that boundary are attacker-supplied
    and deliberately never read. Falls back to request.client.host if the
    header is missing or shorter than expected (a direct hit that
    bypassed the proxy, or a proxy not setting the header -- fixable at
    the proxy, not a reason to trust an unverified value instead).
    """
    trusted_hops = get_settings().TRUSTED_PROXY_COUNT
    if trusted_hops > 0:
        header = request.headers.get("x-forwarded-for")
        if header:
            hops = [hop.strip() for hop in header.split(",") if hop.strip()]
            if len(hops) >= trusted_hops:
                return hops[-trusted_hops]
    return request.client.host if request.client else "unknown"
