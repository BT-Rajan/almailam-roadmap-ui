from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

# Each key corresponds to exactly one email-sending call site in the
# codebase (see email_template_service.DEFAULT_TEMPLATES for the map).
# Unlike DocumentTemplate, these aren't admin-creatable/deletable --
# there is always exactly one row per key, seeded by migration 0069
# (contract_otp/contract_signed seeded separately by migration 0071)
# with the app's original hardcoded copy so behavior is unchanged until
# an admin edits one.
EMAIL_TEMPLATE_KEYS = (
    "client_onboarding_otp",
    "client_welcome",
    "project_created",
    "requirement_otp",
    "requirement_confirmed",
    "quotation_otp",
    "quotation_approved",
    "contract_otp",
    "contract_signed",
    "handover_otp",
    "permit_application_submitted",
    "permit_response_received",
    "payment_received",
    "payment_reminder",
)


class EmailTemplate(Base, TimestampMixin):
    """Admin-editable subject/body for one of the app's automated
    emails. {{ field }} placeholders (see email_template_service.
    MERGE_FIELD_CATALOG) are substituted with live data at send time --
    same convention as DocumentTemplate's .docx merge fields, just
    plain-text substitution instead of docxtpl, since there's nothing
    to upload here."""

    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    key: Mapped[str] = mapped_column(Enum(*EMAIL_TEMPLATE_KEYS, name="email_template_key"), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
