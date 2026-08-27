from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.file_storage import resolve_path
from app.models.client import Client
from app.models.document import ProjectDocument
from app.models.payment import FinancialAgreement, PaymentObligation
from app.models.project import Project, ProjectSelectedActivity
from app.models.timeline import ProjectTimelineEvent
from app.models.user import User
from app.services import company_service, payment_service


def _require_customer(current_user: User) -> User:
    """Every Customer Portal endpoint goes through this -- role gating
    plus the client_id scope every other function here filters by.
    Rejecting a Customer account with no client_id (shouldn't happen via
    the normal account-creation path, but a corrupt/manually-edited row
    is cheap to guard against) rather than silently returning nothing
    for it, which would look like "you have zero projects" instead of
    the actual misconfiguration."""
    if current_user.role != "Customer" or current_user.client_id is None:
        raise PermissionDeniedError()
    return current_user


def list_projects_for_customer(db: Session, current_user: User) -> list[Project]:
    current_user = _require_customer(current_user)
    return (
        db.query(Project)
        .filter(Project.client_id == current_user.client_id, Project.deleted_at.is_(None))
        .order_by(Project.created_at.desc())
        .all()
    )


def get_project_for_customer(db: Session, current_user: User, project_no: str) -> Project:
    current_user = _require_customer(current_user)
    project = (
        db.query(Project)
        .filter(
            Project.project_no == project_no,
            Project.client_id == current_user.client_id,
            Project.deleted_at.is_(None),
        )
        .first()
    )
    if project is None:
        # Doesn't distinguish "no such project" from "exists but isn't
        # yours" -- a customer scoped to their own client_id can't use
        # this to learn anything about another client's projects either
        # way.
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

    path = resolve_path(document.storage_key)
    # The DB row can outlive the actual file (moved, cleaned up, or --
    # as hit while testing this endpoint -- a record that was never
    # backed by a real upload in the first place). Checking here turns
    # that into the same clean 404 a customer would get for a document
    # that never existed, instead of an unhandled 500 with a raw
    # traceback: FileResponse's own missing-file handling happens at
    # response-streaming time, after normal exception-handler
    # middleware has already run, so it isn't caught cleanly.
    if not path.is_file():
        raise NotFoundError("Document")

    return path, document.original_filename


_STAGE_TO_CUSTOMER_STATUS = {"Requirement", "Quotation", "Contract"}


def _customer_status(project: Project) -> str:
    if project.status == "On Hold":
        return "on-hold"
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
        db.query(FinancialAgreement)
        .filter(FinancialAgreement.project_id == project.id)
        .order_by(FinancialAgreement.id.desc())
        .first()
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
            # No project status ever reaches a terminal "done" state --
            # see models/project.py's PROJECT_STATUSES comment -- so
            # there is no actual completion date to report here.
            "actualEndDate": None,
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
