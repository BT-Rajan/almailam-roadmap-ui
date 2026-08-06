from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.number_series_service import next_number


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    category: str,
    link_route_name: str | None = None,
    link_params: dict[str, str] | None = None,
) -> Notification:
    """Called by other services as a side effect of a real business event
    (task assigned, AI review completed, ...) -- there is no separate
    'notifications' CRUD surface for authoring these directly, the same
    way audit_service.log_event isn't called by hand either. Does not
    commit; the caller's own transaction covers this row too."""
    notification = Notification(
        notification_no=next_number(db, "NOTIFICATION"),
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        created_at=datetime.now(timezone.utc),
        read=False,
        link_route_name=link_route_name,
        link_params=link_params,
    )
    db.add(notification)
    return notification


def list_for_user(db: Session, user_id: int, unread_only: bool = False) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.read.is_(False))
    return query.order_by(Notification.created_at.desc()).all()


def mark_as_read(db: Session, user_id: int, notification_no: str) -> None:
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.notification_no == notification_no
    ).update({"read": True})
    db.commit()


def mark_all_as_read(db: Session, user_id: int) -> None:
    db.query(Notification).filter(Notification.user_id == user_id, Notification.read.is_(False)).update(
        {"read": True}
    )
    db.commit()


def delete_notification(db: Session, user_id: int, notification_no: str) -> None:
    # Scoped to the requesting user's own notifications -- notification_no
    # alone isn't checked against ownership by the caller, so this must be.
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.notification_no == notification_no
    ).delete()
    db.commit()


def clear_all(db: Session, user_id: int) -> None:
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.commit()
