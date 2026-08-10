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

    # Controls the `Secure` attribute on the refresh-token cookie. Left
    # unset (None) by default, in which case it falls back to is_production
    # -- but browsers silently drop Secure cookies over plain HTTP, so any
    # box that is ENV=production but served without TLS (e.g. a bare IP
    # deployment) needs to explicitly set COOKIE_SECURE=false in its .env.
    # Deliberately decoupled from ENV/is_production, which also gates the
    # JWT_SECRET_KEY strength check below and shouldn't be weakened just to
    # work around a transport issue.
    COOKIE_SECURE: bool | None = None

    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    UPLOADS_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Real LLM provider credentials -- deliberately environment-only, never
    # stored in the database (see ai_provider_configs, which only ever
    # stores a masked hint of a key, not the key itself). Empty by default;
    # AI features honestly report themselves as unavailable until one of
    # these is set. See app/services/ai_service.py.
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"

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


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a random value of at least 32 characters in production."
        )
    return settings
