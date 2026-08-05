from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

NOTIFICATION_CATEGORIES = ("Project", "Task", "Government", "AI", "System")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    notification_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(*NOTIFICATION_CATEGORIES, name="notification_category"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_route_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    link_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
