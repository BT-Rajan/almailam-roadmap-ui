import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, NotFoundError
from app.core.security import create_access_token, decode_token
from app.models.client import Client, ClientContact
from app.models.document import ProjectDocument
from app.models.project import Project
from app.models.timeline import ProjectTimelineEvent
from app.models.user import User
from app.services import company_service

# Customer portal tokens are deliberately longer-lived than staff access
# tokens (customers browsing their project shouldn't get logged out after
# 15 minutes), and are their own token "type" so they can never be used
# to call any staff-facing endpoint even if somehow presented there --
# get_current_user (app/api/deps.py) only accepts type == "access".
CUSTOMER_PORTAL_TOKEN_TYPE = "customer_portal"
CUSTOMER_PORTAL_TOKEN_EXPIRE_MINUTES = 60


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
    can't be used to enumerate valid project IDs."""
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if not project:
        return None

    client = db.query(Client).filter(Client.id == project.client_id, Client.deleted_at.is_(None)).first()
    if not client:
        return None

    candidates = [client.mobile]
    contacts = db.query(ClientContact).filter(ClientContact.client_id == client.id).all()
    candidates.extend(contact.mobile for contact in contacts)

    if not any(_mobile_matches(candidate, mobile_number) for candidate in candidates):
        return None

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
    "task": "general",
}


def get_project_view(db: Session, project: Project) -> dict:
    client = db.query(Client).filter(Client.id == project.client_id).first()
    engineer = db.query(User).filter(User.id == project.engineer_id).first()
    settings = company_service.get_settings(db)

    events = (
        db.query(ProjectTimelineEvent)
        .filter(ProjectTimelineEvent.project_id == project.id)
        .order_by(ProjectTimelineEvent.event_date.asc())
        .all()
    )
    documents = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project.id, ProjectDocument.deleted_at.is_(None))
        .order_by(ProjectDocument.upload_date.asc())
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

    return {
        "project": {
            "projectId": project.project_no,
            "projectName": project.project_name,
            "description": f"{project.service} for {client.company_name if client else 'the client'}.",
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
    }
