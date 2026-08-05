from datetime import datetime

from pydantic import BaseModel


class NotificationLinkOut(BaseModel):
    routeName: str
    params: dict[str, str] | None = None


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str
    category: str
    date: datetime
    read: bool
    link: NotificationLinkOut | None = None

    @staticmethod
    def from_model(notification) -> "NotificationOut":
        link = (
            NotificationLinkOut(routeName=notification.link_route_name, params=notification.link_params)
            if notification.link_route_name
            else None
        )
        return NotificationOut(
            id=notification.notification_no,
            title=notification.title,
            message=notification.message,
            category=notification.category,
            date=notification.created_at,
            read=notification.read,
            link=link,
        )
