import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, NotFoundError
from app.core.file_storage import resolve_path
from app.core.lockout import LockoutTracker
from app.core.security import create_access_token, decode_token
from app.models.client import Client, ClientContact
from app.models.document import ProjectDocument
from app.models.payment import FinancialAgreement, PaymentObligation
from app.models.project import Project, ProjectSelectedActivity
from app.models.timeline import ProjectTimelineEvent
from app.models.user import User
from app.services import company_service, payment_service

# Customer portal tokens are deliberately longer-lived than staff access
# tokens (customers browsing their project shouldn't get logged out after
# 15 minutes), and are their own token "type" so they can never be used
# to call any staff-facing endpoint even if somehow presented there --
# get_current_user (app/api/deps.py) only accepts type == "access".
CUSTOMER_PORTAL_TOKEN_TYPE = "customer_portal"
CUSTOMER_PORTAL_TOKEN_EXPIRE_MINUTES = 60

# Unlike staff login (5 attempts / 15 min, persisted on the user row via
# failed_login_attempts/locked_until), there's no account row per portal
# visitor to persist a counter on -- this is keyed by project instead,
# in-memory, same trade-off as core/rate_limit.py. Without this, the
# only thing standing between an attacker and brute-forcing the last-9-
# digits mobile match for a known project ID was the blanket 300 req/min
# IP limiter, which is far too loose for a single-field guessing attack.
_verify_lockout = LockoutTracker(max_attempts=5, lockout_seconds=15 * 60)


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _mobile_matches(candidate: str, input_mobile: str) -> bool:
    # Compares the last 9 digits so formatting differences (+971 vs 0
    # prefix, spaces, dashes) don't block a legitimate match.
    candidate_digits = _digits(candidate)[-9:]
    input_digits = _digits(input_mobile)[-9:]
    return bool(candidate_digits) and candidate_digits == input_digits


def verify_and_issue_token(db: Session, project_no: str, mobile_number: str) -> str | None:
    """Returns an access token if the mobile number matches the client's
    own number or one of their contacts' numbers for this project, else
    None. Deliberately does not distinguish "project not found" from
    "mobile didn't match" in what it returns, mirroring the generic
    failure message auth_service.py uses for staff login -- so this
    can't be used to enumerate valid project IDs.

    Lockout is only tracked once a real project is resolved: a made-up
    project_no can't grow the tracker or lock anything, since there's
    nothing real to protect there."""
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if not project:
        return None

    lockout_key = f"portal-verify:{project.id}"
    seconds_locked = _verify_lockout.seconds_locked(lockout_key)
    if seconds_locked:
        minutes = max(1, int(seconds_locked // 60) + 1)
        raise AuthError(f"Too many failed attempts. Try again in {minutes} minute(s).")

    client = db.query(Client).filter(Client.id == project.client_id, Client.deleted_at.is_(None)).first()
    if not client:
        _verify_lockout.register_failure(lockout_key)
        return None

    candidates = [client.mobile]
    contacts = (
        db.query(ClientContact)
        .filter(ClientContact.client_id == client.id, ClientContact.deleted_at.is_(None))
        .all()
    )
    candidates.extend(contact.mobile for contact in contacts)

    if not any(_mobile_matches(candidate, mobile_number) for candidate in candidates):
        _verify_lockout.register_failure(lockout_key)
        return None

    _verify_lockout.register_success(lockout_key)

    return create_access_token(
        subject=str(project.id),
        extra_claims={"type": CUSTOMER_PORTAL_TOKEN_TYPE, "projectNo": project.project_no},
        expire_minutes=CUSTOMER_PORTAL_TOKEN_EXPIRE_MINUTES,
    )


def get_project_for_token(db: Session, token: str, requested_project_no: str) -> Project:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthError("Invalid or expired access link. Please verify your access again.") from exc

    if payload.get("type") != CUSTOMER_PORTAL_TOKEN_TYPE:
        raise AuthError("Invalid access token.")
    if payload.get("projectNo") != requested_project_no:
        raise AuthError("This access link is not valid for the requested project.")

    project = db.query(Project).filter(Project.id == int(payload["sub"]), Project.deleted_at.is_(None)).first()
    if not project:
        raise NotFoundError("Project")
    return project


def get_document_download_target(db: Session, project: Project, document_id: str) -> tuple:
    """A customer can only ever download documents that belong to their
    own (token-verified) project, and only once something has actually
    been shared with them -- a "Draft" is purely internal work-in-
    progress and was never delivered, so it stays off-limits here even
    though staff can see it in the main app."""
    try:
        numeric_id = int(document_id.removeprefix("DOC-")) if document_id.upper().startswith("DOC-") else int(document_id)
    except ValueError as exc:
        raise NotFoundError("Document") from exc

    document = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.id == numeric_id,
            ProjectDocument.project_id == project.id,
            ProjectDocument.deleted_at.is_(None),
        )
        .first()
    )
    if document is None:
        raise NotFoundError("Document")
    if document.status == "Draft":
        raise AuthError("This document isn't available yet.")

    return resolve_path(document.storage_key), document.original_filename


_STAGE_TO_CUSTOMER_STATUS = {"Enquiry", "Quotation", "Contract"}


def _customer_status(project: Project) -> str:
    if project.status == "On Hold":
        return "on-hold"
    if project.status == "Completed":
        return "completed"
    if project.status == "Cancelled":
        return "cancelled"
    if project.current_stage in _STAGE_TO_CUSTOMER_STATUS:
        return "planning"
    return "active"


_MILESTONE_STATUS_MAP = {"completed": "completed", "in-progress": "in-progress", "upcoming": "pending"}
_DELIVERABLE_STATUS_MAP = {
    "Draft": "pending",
    "Under Review": "delivered",
    "Approved": "approved",
    "Rejected": "revision",
}
_UPDATE_TYPE_MAP = {
    "stage": "status",
    "milestone": "milestone",
    "document": "deliverable",
    "note": "general",
    "submission": "general",
    "quotation": "general",
    "contract": "general",
    "task": "general",
}


def get_project_view(db: Session, project: Project) -> dict:
    client = db.query(Client).filter(Client.id == project.client_id).first()
    engineer = db.query(User).filter(User.id == project.engineer_id).first()
    settings = company_service.get_settings(db)

    events = (
        db.query(ProjectTimelineEvent)
        .filter(
            ProjectTimelineEvent.project_id == project.id,
            # field_activity entries are internal site-supervision notes
            # (see status_report_service.attach_report) -- not something
            # to surface on the client-facing "Recent Updates" feed.
            ProjectTimelineEvent.type != "field_activity",
        )
        .order_by(ProjectTimelineEvent.event_date.asc())
        .all()
    )
    documents = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project.id, ProjectDocument.deleted_at.is_(None))
        .order_by(ProjectDocument.upload_date.asc())
        .all()
    )
    activities = (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.project_id == project.id)
        .order_by(ProjectSelectedActivity.service_name.asc(), ProjectSelectedActivity.activity_name.asc())
        .all()
    )

    today = datetime.now(timezone.utc).date()
    milestones = [
        {
            "id": f"TLE-{event.id:03d}",
            "title": event.title,
            "description": event.description,
            "dueDate": event.event_date,
            "status": (
                "delayed"
                if event.status == "upcoming" and event.event_date < today
                else _MILESTONE_STATUS_MAP[event.status]
            ),
            "completedDate": event.event_date if event.status == "completed" else None,
        }
        for event in events
        if event.type in ("milestone", "stage")
    ]

    deliverables = [
        {
            "id": f"DOC-{document.id:03d}",
            "name": document.title,
            "description": None,
            "type": document.type,
            "status": _DELIVERABLE_STATUS_MAP[document.status],
            "deliveryDate": document.upload_date,
            "approvalDate": document.upload_date if document.status == "Approved" else None,
        }
        for document in documents
    ]

    updates = [
        {
            "id": f"TLE-{event.id:03d}",
            "date": event.event_date,
            "title": event.title,
            "description": event.description or event.title,
            "type": _UPDATE_TYPE_MAP.get(event.type, "general"),
        }
        for event in reversed(events)
    ]

    completed_milestones = sum(1 for m in milestones if m["status"] == "completed")
    summary = (
        f"{project.service} engagement currently in the {project.current_stage} stage, "
        f"{project.progress}% complete. {completed_milestones} of {len(milestones)} tracked "
        f"milestones are complete."
        if milestones
        else f"{project.service} engagement currently in the {project.current_stage} stage, "
        f"{project.progress}% complete."
    )

    # Groups the flat selected-activities rows by service, e.g.
    # {"Structural Design": ["Foundation Analysis", "Beam Sizing"], ...}
    # -- "what activities are covered" reads as scope-of-work coverage,
    # not a price list (the budget section below is where the money
    # lives), so this deliberately omits each activity's fixed_cost.
    activities_by_service: dict[str, list[str]] = {}
    for activity in activities:
        activities_by_service.setdefault(activity.service_name, []).append(activity.activity_name)
    activity_groups = [
        {"serviceName": service_name, "activities": activity_names}
        for service_name, activity_names in activities_by_service.items()
    ]

    budget = None
    agreement = (
        db.query(FinancialAgreement).filter(FinancialAgreement.project_id == project.id).first()
    )
    if agreement:
        obligations = payment_service.get_obligations(db, agreement.id)
        total_paid = sum(float(o.amount_received) for o in obligations)
        budget = {
            "contractAmount": float(agreement.contract_amount),
            "currency": agreement.currency,
            "totalPaid": total_paid,
            "totalDue": float(agreement.contract_amount) - total_paid,
            # "Upcoming" -- due, not yet fully paid, not cancelled/waived.
            # Sorted soonest-first, since that's the order a client cares
            # about ("what do I owe and when"), not creation order.
            "upcomingPayments": sorted(
                (
                    {
                        "description": o.description,
                        "amountDue": float(o.amount_due),
                        "amountReceived": float(o.amount_received),
                        "dueDate": o.due_date,
                    }
                    for o in obligations
                    if o.manual_status is None and float(o.amount_received) < float(o.amount_due)
                ),
                key=lambda o: o["dueDate"],
            ),
        }

    return {
        "project": {
            "projectId": project.project_no,
            "projectName": project.project_name,
            "description": project.description or f"{project.service} for {client.company_name if client else 'the client'}.",
            "clientName": client.company_name if client else "Unknown Client",
            "startDate": project.start_date,
            "expectedEndDate": project.target_date,
            "actualEndDate": project.target_date if project.status == "Completed" else None,
            "status": _customer_status(project),
            "progress": project.progress,
            "summary": summary,
            "engineerName": engineer.full_name if engineer else "Al Mailam Team",
            "supportEmail": settings.email or "info@almailam.example",
            "supportPhone": settings.phone or "",
        },
        "milestones": milestones,
        "deliverables": deliverables,
        "updates": updates,
        "activities": activity_groups,
        "budget": budget,
    }
