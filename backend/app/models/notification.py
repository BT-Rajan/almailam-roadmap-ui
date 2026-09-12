from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

NOTIFICATION_CATEGORIES = ("Project", "Task", "Government", "Payment", "AI", "System")


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
    # Router *query* to attach on top of link_params' path params -- e.g.
    # {"tab": "quotation"} so a "Quotation approved" notification opens
    # ProjectWorkspacePage directly on its Quotation view instead of
    # always landing on the generic Requirement/Overview default every
    # project-workspace link otherwise lands on (see ProjectWorkspacePage.
    # vue's own comment on activeTab/stageContext). Kept as a distinct
    # column rather than folded into link_params: that dict fills named
    # path segments (:projectId), and a stray key with no matching
    # segment is silently dropped by vue-router, not carried as a query
    # string -- the two need to stay separate to both actually work.
    link_query: Mapped[dict | None] = mapped_column(JSON, nullable=True)
