"""Site Engineer Portal's status reports -- digitizes the paper
"تقرير إشراف" (Supervision Report) form. Two sides:

  - The filing engineer: list their own projects, file/edit *today's*
    report, view their own report history (list_reports_for_engineer,
    used for the portal's read-only calendar).
  - The designated recipient (CompanySettings.status_report_recipient_id):
    review incoming reports (list_inbox) and attach one to the relevant
    project as a real timeline entry (attach_report) -- project, task,
    reporter name, and date/time all come from the report itself; only
    the recipient's own notes are freshly typed.
"""

from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_bytes
from app.core.kuwait_time import kuwait_now, kuwait_today
from app.models.project import Project
from app.models.status_report import MAX_REPORT_IMAGES, StatusReport, StatusReportImage
from app.models.task import Task
from app.models.user import User
from app.services import company_service, notification_service, task_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "STATUS_REPORT"

# Deliberately hardcoded via core.kuwait_time, not read from
# CompanySettings.timezone -- that setting is a general display
# preference (invoices, dashboards, and defaults to "Asia/Dubai"
# today) that an admin can change at any time for unrelated reasons.
# The daily report cutoff is a specific, stated business rule
# ("editable until 11:59 PM Kuwait time, wherever the engineer
# physically is"), not a display preference -- it must not silently
# shift if someone later changes the company's display timezone.
# Kuwait is UTC+3; Dubai is UTC+4, so conflating the two would move
# the real cutoff by an hour. Same reasoning core.kuwait_time itself
# documents for every other date-sensitive business decision that now
# shares it (payment obligation overdue status, quotation/contract
# expiry, and so on) -- none of them should drift just because someone
# changes the company's display timezone either.

# A cancelled project is finished -- no more field activity is expected
# on it, so no new/edited reports either, independent of what
# start_date/target_date happen to say.
_CLOSED_PROJECT_STATUSES = ("Cancelled",)

# Same bundled-font reasoning as pdf_render.py's own FONT_PATH: the
# server this runs on isn't guaranteed to have any font installed via
# fontconfig, and engineer names are written in Arabic in practice (see
# StatusReport's own docstring) -- a silently-substituted Latin-only
# font would render those as boxes/garbage on the stamped photo. Reuses
# the exact same bundled file already shipped for PDF rendering rather
# than adding a second font dependency; Noto Naskh Arabic also covers
# basic Latin, so the same font works for an English name too.
_STAMP_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf"


def _today(db: Session) -> date:
    """"Today" for report-filing purposes is always Kuwait local time,
    never the server's system clock or the engineer's device clock.
    Matters specifically because this app's servers commonly run on
    UTC: an engineer filing a report between roughly midnight and 3am
    Kuwait time is still the *previous* calendar day in UTC, so
    date.today() there would silently treat a genuinely new day's
    report as an edit to yesterday's already-filed one -- exactly the
    "only today's report is editable, until 11:59 PM Kuwait time"
    rule failing in the one window it actually matters. The `db`
    parameter is unused now (kept so callers don't need to change) --
    see the module comment above for why this doesn't read
    CompanySettings.timezone. Delegates to core.kuwait_time, which
    every other date-sensitive decision in the app now shares.
    """
    return kuwait_today()


def _now(db: Session) -> datetime:
    """Same Kuwait-time convention as _today() above, but with the time
    of day too -- for stamping a report photo with the actual moment it
    was uploaded (status_report_service.stamp_report_image), not just
    the report's own report_date (date only, no time)."""
    return kuwait_now()


def report_filing_today(db: Session) -> date:
    """Public wrapper around _today() -- for callers outside this module
    (e.g. the API layer, computing per-project filing-window state)
    that need "today" by the same clock this module uses internally,
    without reaching into a private helper."""
    return _today(db)


def filing_window_block_reason(project: Project, report_date: date) -> str | None:
    """None if `report_date` is a valid day to file/edit a report for
    this project; otherwise a user-facing reason it isn't. Shared by
    the actual filing gate (file_todays_report) and by the projects
    list (so the portal can show/disable the right thing before the
    engineer even opens the form, not just reject on submit).

    A project with Supervision activities selected files against its
    own Supervision engagement window (supervision_start_date/
    supervision_end_date -- see Project model and project_service.
    _create_service_tasks) instead of the project's overall start_date/
    target_date: those cover every track the project includes (Design,
    Government Submission, Supervision too) and can easily run on a
    different schedule than Supervision itself actually does, so a
    project whose Design work starts well before its Supervision
    engagement would otherwise open report filing far too early. This
    is also what makes a project "go live" for daily field reporting
    right as it reaches the Supervision stage (contract signed with
    Supervision): supervision_start_date is only ever in the past by
    the time Supervision is genuinely under way. A project with no
    Supervision activities keeps the original project-wide window, and
    an open-ended engagement (no supervision_end_date set yet) has no
    upper bound.

    Checked live against the project's *current* dates rather than a
    value captured once, so an extension automatically widens the
    window with no extra code, and the same is true in reverse if it's
    ever pulled in. A closed project (Completed/Cancelled) blocks
    filing outright, even for a date that would otherwise be in range --
    once the project is actually finished there's nothing left to
    report on regardless of what the planned dates say.
    """
    if project.status in _CLOSED_PROJECT_STATUSES:
        return "This project is closed. Status reports can no longer be filed for it."

    if project.supervision_start_date is not None:
        if report_date < project.supervision_start_date:
            return "This project's Supervision engagement hasn't started yet."
        if project.supervision_end_date is not None and report_date > project.supervision_end_date:
            return "This project's Supervision report filing window has closed."
        return None

    if report_date < project.start_date:
        return "This project hasn't started yet."
    if report_date > project.target_date:
        return "This project's report filing window has closed."
    return None


def list_engineer_projects(db: Session, engineer_id: int) -> list[Project]:
    """Projects to offer in the report-filing project picker.

    Two ways a project belongs here, not just one: the project's own
    overall engineer (Project.engineer_id) -- unchanged from before --
    plus any project where this person is specifically assigned to a
    Supervision task (Task.assigned_to), even if they aren't the
    project's overall engineer. That second case is what makes
    delegated day-to-day site supervision actually work: a senior
    engineer can run a project (Project.engineer_id) while a site
    engineer is assigned the Supervision task itself and needs to file
    reports against it too. Without this, list_reports_for_task's own
    Supervision-task matching (Task.assigned_to == report.engineer_id)
    could never be satisfied for that site engineer, since they'd never
    even see the project in this picker to file a report in the first
    place.

    Deliberately not status-filtered on either path (an engineer might
    legitimately still be filing a report against a project mid-
    handover even if its status just changed) -- this is a picker
    convenience, not a business-rule gate.
    """
    supervision_project_ids = (
        db.query(Task.project_id)
        .filter(Task.assigned_to == engineer_id, Task.linked_stage_type == "Supervision", Task.deleted_at.is_(None))
        .distinct()
    )
    return (
        db.query(Project)
        .filter(
            Project.deleted_at.is_(None),
            or_(Project.engineer_id == engineer_id, Project.id.in_(supervision_project_ids)),
        )
        .order_by(Project.project_name.asc())
        .all()
    )


def get_todays_report_for_project(db: Session, engineer_id: int, project_id: int) -> StatusReport | None:
    return (
        db.query(StatusReport)
        .filter(
            StatusReport.engineer_id == engineer_id,
            StatusReport.project_id == project_id,
            StatusReport.report_date == _today(db),
        )
        .first()
    )


def list_todays_reports(db: Session, engineer_id: int) -> list[StatusReport]:
    """Every report this engineer has already filed today, across all
    their projects -- one engineer assigned to several projects files a
    separate report per project each day, so "today's report" is
    genuinely plural here. Used to show, per project, whether today's
    report is already filed (and pre-fillable for editing) or still
    outstanding."""
    return (
        db.query(StatusReport)
        .filter(StatusReport.engineer_id == engineer_id, StatusReport.report_date == _today(db))
        .order_by(StatusReport.project_id.asc())
        .all()
    )


def list_reports_for_engineer(db: Session, engineer_id: int, start: date, end: date) -> list[StatusReport]:
    """Backs the portal's read-only calendar -- start/end define the
    visible month (or whatever range the frontend requests)."""
    return (
        db.query(StatusReport)
        .filter(
            StatusReport.engineer_id == engineer_id,
            StatusReport.report_date >= start,
            StatusReport.report_date <= end,
        )
        .order_by(StatusReport.report_date.desc())
        .all()
    )


def file_todays_report(
    db: Session,
    engineer_id: int,
    project_no: str,
    receipt_type: str | None,
    supervision_type: str,
    notes: str,
) -> StatusReport:
    """Create-or-update-today's-row *for this project* -- "file today's
    report" is a single action regardless of whether one already exists
    for today for this particular project, not a separate create vs.
    edit decision the caller has to make. An engineer assigned to
    several projects calls this once per project per day; each call is
    scoped independently by (engineer, project, day), so filing today's
    report for Project A has no effect on Project B's. Deliberately
    blocked once the report has already been reviewed and attached (see
    attach_report) -- at that point it's become the permanent basis for
    a real project timeline entry, and silently changing it out from
    under that record would make the timeline entry describe a report
    that no longer exists in its original form."""
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.is_(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Project")

    if not notes.strip():
        raise ValidationAppError("Notes are required.")

    today = _today(db)
    block_reason = filing_window_block_reason(project, today)
    if block_reason:
        raise ValidationAppError(block_reason)

    existing = get_todays_report_for_project(db, engineer_id, project.id)
    if existing:
        if existing.status == "Attached":
            raise ValidationAppError(
                "Today's report for this project has already been reviewed and attached -- it can no longer be edited."
            )
        existing.receipt_type = receipt_type
        existing.supervision_type = supervision_type
        existing.notes = notes
        db.commit()
        db.refresh(existing)
        return existing

    report = StatusReport(
        report_no=next_number(db, "STATUS_REPORT"),
        project_id=project.id,
        engineer_id=engineer_id,
        report_date=today,
        receipt_type=receipt_type,
        supervision_type=supervision_type,
        notes=notes,
        status="Pending",
    )
    db.add(report)
    db.flush()

    # "the designated person will receive it" -- a passive inbox nobody
    # gets told to check isn't really receiving anything. Only fires for
    # a genuinely new report, not every edit to today's -- editing an
    # already-pending report doesn't need a second notification for the
    # same thing.
    settings = company_service.get_settings(db)
    if settings.status_report_recipient_id:
        engineer = db.query(User).filter(User.id == engineer_id).first()
        notification_service.create_notification(
            db, settings.status_report_recipient_id,
            "New status report received",
            f"{engineer.full_name if engineer else 'A site engineer'} filed a status report for {project.project_name}.",
            "System",
            link_route_name="status-reports-inbox",
        )

    db.commit()
    db.refresh(report)
    return report


def list_reports_for_project(db: Session, project_id: int) -> list[StatusReport]:
    """Every report filed against this project, Pending or Attached,
    across whichever engineer(s) filed them -- backs the read-only
    calendar shown on the project's own Supervision > Documents tab
    (distinct from list_reports_for_engineer above, which is scoped the
    other way, to one engineer's own portal calendar across all their
    projects)."""
    return (
        db.query(StatusReport)
        .filter(StatusReport.project_id == project_id)
        .order_by(StatusReport.report_date.desc())
        .all()
    )


def list_reports_for_task(db: Session, task: Task) -> list[StatusReport]:
    """Every field report relevant to this specific task -- the "task
    history" shown on a task once it's assigned to a site engineer.

    Supervision-track tasks (linked_stage_type == "Supervision") show
    every report the assigned engineer has filed for the task's
    project, full stop -- not only the ones a recipient happened to
    manually pick this exact task for in attach_report's optional task
    picker. These reports (see this module's own docstring -- they
    digitize the paper "تقرير إشراف" / Supervision Report form) are
    inherently supervision documentation for the project regardless of
    whether anyone has reviewed and attached them yet, so gating
    visibility on that separate, easy-to-skip review step was losing
    reports from the one place -- the Supervision task -- where staff
    would actually go looking for them. Pending (not yet reviewed)
    reports appear here too, alongside Attached ones.

    Design/Permit tasks have no such project-wide report stream to draw
    on, so they keep the narrower original behavior: only reports this
    exact task was explicitly chosen for during attach.
    """
    if task.linked_stage_type == "Supervision":
        return (
            db.query(StatusReport)
            .filter(StatusReport.project_id == task.project_id, StatusReport.engineer_id == task.assigned_to)
            .order_by(StatusReport.report_date.desc())
            .all()
        )
    return (
        db.query(StatusReport)
        .filter(StatusReport.attached_task_id == task.id)
        .order_by(StatusReport.report_date.desc())
        .all()
    )


def list_inbox(db: Session) -> list[StatusReport]:
    """Every report not yet reviewed, oldest first -- the recipient's
    queue, not scoped to any one project since a single recipient
    handles reports across whichever projects come in."""
    return (
        db.query(StatusReport)
        .filter(StatusReport.status == "Pending")
        .order_by(StatusReport.report_date.asc(), StatusReport.id.asc())
        .all()
    )


def get_report(db: Session, report_id: int) -> StatusReport:
    report = db.query(StatusReport).filter(StatusReport.id == report_id).first()
    if report is None:
        raise NotFoundError("Status report")
    return report


def attach_report(db: Session, report_id: int, task_no: str | None, recipient_notes: str, actor_id: int) -> StatusReport:
    """Turns a filed report into a real project timeline entry. Project,
    task (if given), reporter name, and report date/time are all pulled
    from the report itself -- recipient_notes is the only thing typed
    fresh here."""
    report = get_report(db, report_id)
    if report.status == "Attached":
        raise ValidationAppError("This report has already been attached.")
    if not recipient_notes.strip():
        raise ValidationAppError("Notes are required to attach a report.")

    task: Task | None = None
    if task_no:
        task = task_service.get_task(db, task_no)
        if task.project_id != report.project_id:
            raise ValidationAppError("The selected task does not belong to this report's project.")
        # Only for Supervision tasks -- their visibility rule
        # (list_reports_for_task) matches by the task's own assignee,
        # not by whatever gets attached here, so attaching to a
        # Supervision task assigned to someone other than this report's
        # engineer would "succeed" here and then the report would never
        # actually show up on that task. Design/Permit tasks match
        # directly on attached_task_id regardless of assignee, so
        # there's no such trap for those.
        if task.linked_stage_type == "Supervision" and task.assigned_to != report.engineer_id:
            raise ValidationAppError(
                "This Supervision task is assigned to a different engineer than the one who filed this report -- "
                "the report would not appear on that task's history. Choose a task assigned to this report's engineer, "
                "or leave the task unselected."
            )

    engineer = db.query(User).filter(User.id == report.engineer_id).first()
    engineer_name = engineer.full_name if engineer else "Unknown"

    description_parts = [
        f"Field report by {engineer_name} on {report.report_date.isoformat()}.",
    ]
    if report.receipt_type:
        description_parts.append(f"Receipt/Handover: {report.receipt_type}")
    description_parts.append(f"Supervision: {report.supervision_type}")
    if task:
        description_parts.append(f"Task: {task.task_no} — {task.title}")
    description_parts.append(f"Report notes: {report.notes}")
    description_parts.append(f"Reviewer notes: {recipient_notes.strip()}")

    event = timeline_service.create_system_event(
        db,
        report.project_id,
        "field_activity",
        f"Field activity reported by {engineer_name}",
        "\n\n".join(description_parts),
        actor_id,
    )
    db.flush()

    report.status = "Attached"
    report.attached_task_id = task.id if task else None
    report.attached_timeline_event_id = event.id
    report.attached_by = actor_id
    report.attached_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report


def stamp_report_image(contents: bytes, engineer_name: str, project_no: str, stamped_at: datetime) -> bytes:
    """Burns the filing engineer's name, project number, and the exact
    date/time of upload directly into the photo's pixels (a banner
    across the bottom), not just alongside it as separate metadata --
    the point is that the stamp travels with the image itself wherever
    it's downloaded, printed, or forwarded, the same as a handwritten
    caption would have on the paper form this digitizes. Re-encodes as
    JPEG regardless of the source format, so every stored report photo
    is a consistent, predictable type.
    """
    image = Image.open(BytesIO(contents))
    # Respects the phone camera's own orientation tag -- without this a
    # portrait photo opened by a library that ignores EXIF (most do)
    # comes out sideways, since the raw pixel data is often stored
    # landscape with a rotation flag rather than pre-rotated.
    image = ImageOps.exif_transpose(image)
    if image.mode != "RGB":
        image = image.convert("RGB")

    lines = [
        engineer_name,
        f"Project: {project_no}",
        stamped_at.strftime("%d %b %Y, %H:%M") + " Kuwait time",
    ]

    font_size = max(16, image.width // 32)
    try:
        font = ImageFont.truetype(str(_STAMP_FONT_PATH), font_size)
    except OSError:
        # Same "don't fail the whole upload over a font problem" spirit
        # as _today()/_now()'s own tz fallback -- a smaller, uglier
        # stamp is far better than the photo not saving at all.
        font = ImageFont.load_default()

    padding = font_size // 2
    line_height = int(font_size * 1.3)
    banner_height = line_height * len(lines) + padding * 2

    draw = ImageDraw.Draw(image, "RGBA")
    # 80% transparent (alpha 51/255) at the person's own request, so the
    # banner doesn't mask whatever was actually photographed -- only
    # dark enough to be a hint of where the caption sits, not an opaque
    # bar. A black stroke around the white text (not just a flat fill)
    # is what keeps the caption itself legible now that it's sitting on
    # top of the real photo colors underneath instead of a solid band.
    draw.rectangle([(0, image.height - banner_height), (image.width, image.height)], fill=(0, 0, 0, 51))
    y = image.height - banner_height + padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200))
        y += line_height

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def list_report_images(db: Session, report_id: int) -> list[StatusReportImage]:
    return (
        db.query(StatusReportImage)
        .filter(StatusReportImage.status_report_id == report_id)
        .order_by(StatusReportImage.sequence.asc())
        .all()
    )


def _assert_can_edit_images(report: StatusReport, engineer_id: int) -> None:
    if report.engineer_id != engineer_id:
        raise NotFoundError("Status report")
    if report.status == "Attached":
        raise ValidationAppError("This report has already been reviewed and attached -- photos can no longer be changed.")


def add_report_image(db: Session, report_id: int, engineer_id: int, file: UploadFile) -> StatusReport:
    """Adds one photo to `report_id`, stamped with this engineer's own
    name, the report's project number, and the current date/time (see
    stamp_report_image) -- only the report's own filing engineer can
    add to it (NotFoundError rather than a permission error, so this
    doesn't confirm another engineer's report even exists), and only
    while it's still editable, same rule file_todays_report already
    enforces for the report's own fields. Returns the full report so
    the caller doesn't need a second round trip to see the updated
    image list.
    """
    report = get_report(db, report_id)
    _assert_can_edit_images(report, engineer_id)

    existing = list_report_images(db, report_id)
    if len(existing) >= MAX_REPORT_IMAGES:
        raise ValidationAppError(f"A report can have at most {MAX_REPORT_IMAGES} photos.")

    project = db.query(Project).filter(Project.id == report.project_id).first()
    engineer = db.query(User).filter(User.id == engineer_id).first()

    # Same size cap and "read at most one byte over the limit" pattern
    # as file_storage.save_upload -- read unboundedly here first and a
    # deliberately huge upload gets fully buffered into memory before
    # anything has a chance to reject it.
    max_bytes = get_settings().MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = file.file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise ValidationAppError(f"Photo exceeds the {get_settings().MAX_UPLOAD_SIZE_MB} MB upload limit.")
    if not contents:
        raise ValidationAppError("Uploaded photo is empty.")
    try:
        stamped = stamp_report_image(
            contents,
            engineer.full_name if engineer else "Unknown",
            project.project_no if project else "",
            _now(db),
        )
    except Exception as exc:
        raise ValidationAppError("That file doesn't look like a valid image.") from exc

    storage_key, original_filename, size_bytes = save_bytes(
        stamped, "status_report_images", ".jpg", file.filename or "photo.jpg"
    )
    db.add(
        StatusReportImage(
            status_report_id=report.id,
            storage_key=storage_key,
            original_filename=original_filename,
            file_size_bytes=size_bytes,
            sequence=len(existing) + 1,
        )
    )
    db.commit()
    db.refresh(report)
    return report


def delete_report_image(db: Session, report_id: int, engineer_id: int, image_id: int) -> StatusReport:
    report = get_report(db, report_id)
    _assert_can_edit_images(report, engineer_id)

    image = (
        db.query(StatusReportImage)
        .filter(StatusReportImage.id == image_id, StatusReportImage.status_report_id == report_id)
        .first()
    )
    if image is None:
        raise NotFoundError("Report photo")

    resolve_path(image.storage_key).unlink(missing_ok=True)
    db.delete(image)
    db.commit()
    db.refresh(report)
    return report
