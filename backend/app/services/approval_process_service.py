"""The 5-step Project Approval Process, built as a separate, new,
self-contained trial -- not touching current_stage or
PROJECT_STAGE_ALLOWED_TRANSITIONS in any way. See approval_process.py's
own docstring for the full reasoning.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.approval_process import ApprovalProcessTemplate, ProjectApprovalStep
from app.services import audit_service

ENTITY_TYPE = "PROJECT"


def parse_project_approval_step_id(raw: str) -> int:
    text = raw.removeprefix("PAS-") if raw.upper().startswith("PAS-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid approval step id.")
    return int(text)


def list_template(db: Session) -> list[ApprovalProcessTemplate]:
    return (
        db.query(ApprovalProcessTemplate)
        .filter(ApprovalProcessTemplate.deleted_at.is_(None))
        .order_by(ApprovalProcessTemplate.sequence_number.asc())
        .all()
    )


def snapshot_steps_for_project(db: Session, project_id: int) -> None:
    """Called once, at project creation (project_service.create_project)
    -- copies the current template into this project's own rows. Does
    not commit; the caller's own transaction covers this too, same
    convention as execution_step_service.snapshot_steps_for_project."""
    for template_step in list_template(db):
        db.add(
            ProjectApprovalStep(
                project_id=project_id,
                name=template_step.name,
                sequence_number=template_step.sequence_number,
                status="Pending",
            )
        )


def list_project_steps(db: Session, project_id: int) -> list[ProjectApprovalStep]:
    return (
        db.query(ProjectApprovalStep)
        .filter(ProjectApprovalStep.project_id == project_id)
        .order_by(ProjectApprovalStep.sequence_number.asc())
        .all()
    )


def get_project_step(db: Session, project_id: int, step_id: int) -> ProjectApprovalStep:
    step = (
        db.query(ProjectApprovalStep)
        .filter(ProjectApprovalStep.id == step_id, ProjectApprovalStep.project_id == project_id)
        .first()
    )
    if step is None:
        raise NotFoundError("Approval process step")
    return step


def complete_step(db: Session, project_id: int, step_id: int, user_id: int | None) -> ProjectApprovalStep:
    step = get_project_step(db, project_id, step_id)
    if step.status == "Completed":
        return step

    incomplete_before = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number < step.sequence_number,
            ProjectApprovalStep.status != "Completed",
        )
        .count()
    )
    if incomplete_before > 0:
        raise ValidationAppError(
            "Steps must be completed in order -- finish the steps before this one first."
        )

    step.status = "Completed"
    step.completed_at = datetime.now(timezone.utc)
    step.completed_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Approval process step completed: {step.name}", user_id
    )
    db.commit()
    db.refresh(step)
    return step


def uncomplete_step(db: Session, project_id: int, step_id: int, user_id: int | None) -> ProjectApprovalStep:
    """Undoing a mistake is allowed -- but only for the most recently
    completed step, mirroring execution_step_service's own rule
    exactly, so this checklist can never end up with a completed step
    sitting after an incomplete one."""
    step = get_project_step(db, project_id, step_id)
    if step.status != "Completed":
        return step

    later_completed = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number > step.sequence_number,
            ProjectApprovalStep.status == "Completed",
        )
        .count()
    )
    if later_completed > 0:
        raise ValidationAppError(
            "Only the most recently completed step can be undone -- undo later steps first."
        )

    step.status = "Pending"
    step.completed_at = None
    step.completed_by = None
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Approval process step un-completed: {step.name}", user_id
    )
    db.commit()
    db.refresh(step)
    return step
