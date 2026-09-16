from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.kuwait_time import KUWAIT_TIMEZONE, kuwait_now
from app.schemas.server_time import ServerTimeOut

router = APIRouter(prefix="/api/server-time", tags=["server-time"])


@router.get("", response_model=ServerTimeOut)
def get_server_time(_=Depends(get_current_user)):
    """Any authenticated user, not gated behind a specific module
    permission (Depends(get_current_user), not require_permission) --
    this is infrastructure every date-sensitive screen needs (Payment
    Status, the dashboard, Contract expiry), not a feature area someone
    could reasonably lack access to."""
    now = kuwait_now()
    return ServerTimeOut(date=now.date().isoformat(), datetime=now.isoformat(), timezone=KUWAIT_TIMEZONE)
