from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import ProfileUpdate, UserOut
from app.services import auth_service, user_service

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
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    tokens = auth_service.login(db, payload.username, payload.password)
    set_refresh_cookie(response, tokens["refresh_token"])
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise AuthError("Session expired. Please log in again.")
    tokens = auth_service.refresh(db, refresh_token)
    set_refresh_cookie(response, tokens["refresh_token"])
    return tokens


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


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.from_model(current_user)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = user_service.update_own_profile(db, current_user, payload)
    return UserOut.from_model(user)
