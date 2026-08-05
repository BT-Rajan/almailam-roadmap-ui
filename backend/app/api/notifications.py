from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notifications = notification_service.list_for_user(db, current_user.id)
    return [NotificationOut.from_model(n) for n in notifications]


@router.patch("/{notification_no}/read")
def mark_as_read(
    notification_no: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    notification_service.mark_as_read(db, current_user.id, notification_no)
    return {"message": "Marked as read."}


@router.patch("/read-all")
def mark_all_as_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification_service.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read."}
