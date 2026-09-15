from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

STATUS_REPORT_SUPERVISION_TYPES = ("Full-time", "Part-time")
STATUS_REPORT_STATUSES = ("Pending", "Attached")
# The paper "تقرير إشراف" form this digitizes had room for a handful of
# attached site photos, each captioned by hand -- this is the same
# limit, just enforced instead of merely assumed, and the caption is now
# a printed stamp (see stamp_report_image) instead of handwriting.
MAX_REPORT_IMAGES = 5


class StatusReport(Base, TimestampMixin):
    """A site engineer's daily supervision report, filed through the Site
    Engineer Portal (api/site_portal.py) -- digitizes the paper
    "تقرير إشراف" (Supervision Report) form: report date, the project
    supervised, what was received/inspected, the type of supervision,
    and the engineer's free-text notes (written in Arabic in practice;
    stored as plain Unicode text, no special handling needed).

    One report per engineer *per project* per day (see the unique
    constraint in schema.sql/the migration) -- an engineer assigned to
    several projects files one report per project each day, not a
    single report covering all of them. "File today's report" is a
    create-or-edit-today's-row operation scoped to whichever project is
    selected, not a single row per engineer per day.

    Pending until the designated recipient (CompanySettings.
    status_report_recipient_id) reviews it and attaches it to a project
    timeline entry (status_report_service.attach_report), at which point
    it's locked -- see attached_at/attached_by/timeline_event_id below.
    """

    __tablename__ = "status_reports"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    report_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    engineer_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supervision_type: Mapped[str] = mapped_column(
        Enum(*STATUS_REPORT_SUPERVISION_TYPES, name="status_report_supervision_type"),
        nullable=False,
        default="Full-time",
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*STATUS_REPORT_STATUSES, name="status_report_status"), nullable=False, default="Pending"
    )

    attached_task_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    attached_timeline_event_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_timeline_events.id", ondelete="SET NULL"), nullable=True
    )
    attached_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    attached_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class StatusReportImage(Base):
    """A site photo attached to a StatusReport (up to MAX_REPORT_IMAGES
    above) -- stamped server-side with the filing engineer's name,
    project number, and the exact date/time of the upload (Kuwait time,
    same clock as report filing) before being saved, see
    status_report_service.stamp_report_image. Stored the same way as
    MessageAttachment/ProjectDocument (file_storage's storage_key +
    original_filename + size), its own table for the same reason
    MessageAttachment is its own table rather than reusing
    ProjectDocument: no version history, no stage/exit-criteria
    involvement, just photos belonging to one specific report."""

    __tablename__ = "status_report_images"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    status_report_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("status_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Display order -- 1-indexed in upload order, not reshuffled if an
    # earlier one is deleted (so "photo 3" stays meaningfully "the third
    # one added" rather than being renumbered out from under anyone
    # looking at it mid-review).
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
