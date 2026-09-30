from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.core.kuwait_time import KUWAIT_TIMEZONE, kuwait_now
from app.core.middleware import client_ip
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    SessionBootstrapOut,
    TokenResponse,
)
from app.schemas.company import CompanyBrandingOut
from app.schemas.server_time import ServerTimeOut
from app.schemas.user import CurrentUserOut, ProfileUpdate
from app.services import ai_config_service, auth_service, company_service, role_service, user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

# Scoped to /api/auth rather than the whole API: the browser only needs to
# send this cookie to the refresh/logout endpoints, not on every request.
# httpOnly means JS never touches the raw token, so a stored-XSS bug
# elsewhere in the app can no longer steal it (client-side script can still
# ride the user's session via the cookie for the endpoints it's scoped to,
# but that's what CSRF defenses -- SameSite here -- are for, not what
# httpOnly protects against).
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        # No max_age/expires: this is deliberately a session cookie, not a
        # persistent one. Browsers drop session cookies when the browser
        # itself (not just the tab) is closed, so a closed browser can't
        # come back and silently resume the session. The refresh token's
        # own JWT/DB expiry (REFRESH_TOKEN_EXPIRE_DAYS) still caps how
        # long it would be usable if a browser's "restore previous
        # session" setting keeps the cookie alive across a restart anyway.
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _current_user_out(db: Session, user: User) -> CurrentUserOut:
    return CurrentUserOut.from_model_with_permissions(user, role_service.get_role_permissions(db, user.role))


def _session_bootstrap(db: Session, user: User) -> SessionBootstrapOut:
    now = kuwait_now()
    knowledge_enabled = False
    if role_service.has_permission(db, user.role, "Knowledgebase", "view"):
        config, _providers = ai_config_service.get_configuration(db)
        knowledge_enabled = config.is_enabled
    return SessionBootstrapOut(
        serverTime=ServerTimeOut(date=now.date().isoformat(), datetime=now.isoformat(), timezone=KUWAIT_TIMEZONE),
        branding=CompanyBrandingOut.from_model(company_service.get_settings(db)),
        knowledgeEnabled=knowledge_enabled,
    )


def _token_response(db: Session, tokens: dict) -> TokenResponse:
    """The new access token plus the signed-in user and what the app needs
    to start (see SessionBootstrapOut), so sign-in -- or resuming a session
    on page load -- is the only request before the first page can show."""
    user = tokens["user"]
    return TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        user=_current_user_out(db, user),
        session=_session_bootstrap(db, user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    tokens = auth_service.login(db, payload.username, payload.password, client_ip(request))
    set_refresh_cookie(response, tokens["refresh_token"])
    return _token_response(db, tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise AuthError("Session expired. Please log in again.")
    tokens = auth_service.refresh(db, refresh_token)
    set_refresh_cookie(response, tokens["refresh_token"])
    return _token_response(db, tokens)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        auth_service.logout(db, refresh_token)
    clear_refresh_cookie(response)
    return {"message": "Logged out."}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(
        db, current_user, payload.current_password, payload.new_password
    )
    return {"message": "Password changed. Please log in again."}


@router.get("/me", response_model=CurrentUserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _current_user_out(db, current_user)


# Same shape as GET /me on purpose: the frontend replaces its whole
# signed-in user with this response after a profile edit, so a response
# without `permissions` would silently strip them from the session.
@router.patch("/me", response_model=CurrentUserOut)
def update_me(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = user_service.update_own_profile(db, current_user, payload)
    return _current_user_out(db, user)
