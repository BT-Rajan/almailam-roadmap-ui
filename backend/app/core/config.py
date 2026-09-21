from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "ServiceOS"
    ENV: str = "development"
    DEBUG: bool = False

    # Single-process deployment: the backend serves both the API (under
    # /api) and the built frontend (frontend/dist) on this one port. The
    # installer writes this value and it is the only port anything in the
    # system needs to know about.
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Path to the built frontend (output of `npm run build`, i.e. the repo's
    # dist/ directory), resolved relative to the backend/ working directory
    # by default. When present, main.py mounts it and serves index.html for
    # any non-/api route so the whole app runs as one process on one port.
    FRONTEND_DIST_DIR: str = "../dist"

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "serviceos_user"
    DB_PASSWORD: str = ""
    DB_NAME: str = "serviceos"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Server-side backstop for the frontend's inactivity idle logout
    # (currently 5 minutes -- see useIdleLogout.ts): independent of the
    # client-side activity timer, a refresh token that hasn't actually
    # been used to mint a new access token in this long is treated as an
    # abandoned session, not a live one, even though it isn't outright
    # expired yet. This measures time since the refresh token was last
    # *redeemed* (login or previous refresh), not moment-to-moment
    # activity -- a continuously-active session's first refresh naturally
    # happens right around ACCESS_TOKEN_EXPIRE_MINUTES (that's what forces
    # it), so this has to stay comfortably above that value or every
    # ordinary session gets misread as abandoned on its very first silent
    # refresh (this is what was happening: a long-lived form like the
    # client wizard, with no API calls in between while someone types,
    # would 401 on submit, refresh, and immediately get "Session expired
    # due to inactivity" even though the client-side timer -- the actual
    # real-activity check -- never came close to firing). The frontend's
    # own idle-activity timer is what actually enforces "idle" in the real
    # sense; this backstop only has to not fire before that one already
    # would have, which is why it stays well above ACCESS_TOKEN_EXPIRE_MINUTES
    # rather than tracking the frontend's timeout value directly.
    INACTIVITY_TIMEOUT_MINUTES: int = 45

    # Controls the `Secure` attribute on the refresh-token cookie. Left
    # unset (None) by default, in which case it falls back to is_production
    # -- but browsers silently drop Secure cookies over plain HTTP, so any
    # box that is ENV=production but served without TLS (e.g. a bare IP
    # deployment) needs to explicitly set COOKIE_SECURE=false in its .env.
    # Deliberately decoupled from ENV/is_production, which also gates the
    # JWT_SECRET_KEY strength check below and shouldn't be weakened just to
    # work around a transport issue.
    COOKIE_SECURE: bool | None = None

    # Controls the `SameSite` attribute on the refresh-token cookie.
    # "lax" (the default) only works when the frontend and this API are
    # same-site (same registrable domain -- different ports/subdomains of
    # the same domain are fine, e.g. the single-process deploy where both
    # are served from one origin). The moment they're on genuinely
    # different domains (a separately-hosted frontend calling this API,
    # a staging frontend pointed at a shared backend, etc.), "lax" means
    # the browser silently *won't attach the cookie at all* to the
    # fetch() calls apiClient.ts makes with credentials: 'include' --
    # cross-site requests only get a Lax cookie on top-level navigations,
    # never on XHR/fetch. That shows up as exactly this: no CORS error on
    # the request itself (CORS_ORIGINS being correct is a separate,
    # necessary-but-not-sufficient condition), but /api/auth/refresh 401s
    # every time because request.cookies.get("refresh_token") is simply
    # empty on the server. Set this to "none" for a cross-site deployment
    # -- browsers require Secure whenever SameSite=None (enforced below),
    # so that also means the API must be served over HTTPS.
    COOKIE_SAMESITE: str = "lax"

    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    UPLOADS_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Fallback LLM provider credentials, read only when no key has been
    # saved for that provider from the Knowledgebase AI admin page (see
    # AIProviderConfig.api_key_encrypted / app.core.security.encrypt_secret
    # -- the admin-entered key is encrypted at rest and takes priority over
    # these). Useful for a deploy that wants credentials fixed at the
    # infrastructure level instead of editable from the app. Empty by
    # default; AI features honestly report themselves as unavailable until
    # a key exists via either path. See app/services/ai_service.py.
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # SMTP credentials for emailing a generated Quotation/Contract
    # document (see app/services/email_service.py). Same "empty by
    # default, feature honestly reports itself unavailable until
    # configured" pattern as the LLM keys above. Takes priority over
    # the in-app mailbox configured under Administration -> Email (see
    # app.models.email_settings / app.services.email_settings_service)
    # when SMTP_HOST is set here -- useful for a deploy that wants
    # credentials fixed at the infrastructure level instead of editable
    # from the app.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    # Shown as the message's From: address -- falls back to SMTP_USERNAME
    # (the typical case: authenticating and sending as the same mailbox)
    # when left unset, so most setups only need to set this once.
    SMTP_FROM_ADDRESS: str = ""
    SMTP_USE_TLS: bool = True

    @property
    def smtp_from_address(self) -> str:
        return self.SMTP_FROM_ADDRESS or self.SMTP_USERNAME

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.smtp_from_address)

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        configured = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        # Same-origin requests (frontend served by this same process) don't
        # need CORS at all, but these are added defensively so the app still
        # works if something reaches the API from localhost:<PORT> under a
        # scheme/host combination not already listed in .env.
        implied = [f"http://localhost:{self.PORT}", f"http://127.0.0.1:{self.PORT}"]
        return list(dict.fromkeys(configured + implied))

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production if self.COOKIE_SECURE is None else self.COOKIE_SECURE

    @property
    def cookie_samesite(self) -> str:
        value = self.COOKIE_SAMESITE.strip().lower()
        if value not in ("lax", "strict", "none"):
            raise RuntimeError(
                f"COOKIE_SAMESITE must be one of 'lax', 'strict', or 'none' (got '{self.COOKIE_SAMESITE}')."
            )
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a random value of at least 32 characters in production."
        )
    # Browsers reject/strip a SameSite=None cookie outright unless it's
    # also Secure -- so a cross-site deploy that sets COOKIE_SAMESITE=none
    # without also getting Secure=true (either via COOKIE_SECURE=true or
    # ENV=production with COOKIE_SECURE left unset) would silently trade
    # one broken refresh cookie for another, in a way that's much harder
    # to spot than failing loudly at startup.
    if settings.cookie_samesite == "none" and not settings.cookie_secure:
        raise RuntimeError(
            "COOKIE_SAMESITE=none requires the refresh cookie to be Secure -- "
            "set COOKIE_SECURE=true (and serve the API over HTTPS) or use ENV=production."
        )
    return settings
