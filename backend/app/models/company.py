from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK


class CompanySettings(Base, TimestampMixin):
    __tablename__ = "company_settings"

    # This table only ever holds a single row (id is always 1) -- there is
    # one company-wide configuration, not a list of them.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False, default="Al Mailam Consulting")
    tagline: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    trade_license_number: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(250), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    brand_color: Mapped[str] = mapped_column(String(20), nullable=False, default="#1D4ED8")
    default_language: Mapped[str] = mapped_column(String(20), nullable=False, default="English")
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="Asia/Dubai")
    date_format: Mapped[str] = mapped_column(String(20), nullable=False, default="DD/MM/YYYY")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="AED")
    default_payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    default_quotation_validity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    # Used by the stale-project background check (see
    # project_service.check_and_notify_stale_projects) -- how many days a
    # project can sit without its workflow stage advancing before the
    # assigned engineer is notified.
    stale_project_alert_days: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    # Used by client_service.check_and_notify_stale_onboarding -- how
    # many days a client's onboarding can sit at the same step before
    # the account manager is notified. A much shorter default than
    # stale_project_alert_days deliberately -- onboarding should be a
    # quick process measured in days, not the months a project might
    # reasonably span, so the two are kept as separate settings rather
    # than sharing one knob.
    stale_onboarding_alert_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # Whoever this is set to receives every site-engineer status report
    # for review and attachment to the relevant project (see
    # status_report_service.py) -- nullable because the feature is
    # simply inactive/unrouted until an admin picks someone.
    status_report_recipient_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
