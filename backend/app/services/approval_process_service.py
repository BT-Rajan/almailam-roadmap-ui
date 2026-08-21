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
                stage_key=template_step.stage_key,
                sequence_number=template_step.sequence_number,
                is_optional=template_step.is_optional,
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
    if step.status == "Waived":
        raise ValidationAppError("This step has been waived -- unwaive it first to complete it instead.")

    incomplete_before = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number < step.sequence_number,
            ProjectApprovalStep.status == "Pending",
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
    resolved (Completed or Waived) step, mirroring
    execution_step_service's own rule exactly, so this checklist can
    never end up with a resolved step sitting after an unresolved
    one."""
    step = get_project_step(db, project_id, step_id)
    if step.status != "Completed":
        return step

    later_resolved = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number > step.sequence_number,
            ProjectApprovalStep.status != "Pending",
        )
        .count()
    )
    if later_resolved > 0:
        raise ValidationAppError(
            "Only the most recently completed or waived step can be undone -- undo later steps first."
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


def waive_step(db: Session, project_id: int, step_id: int, reason: str, user_id: int | None) -> ProjectApprovalStep:
    """Mirrors execution_step_service.waive_step exactly -- only
    reachable from Pending, only for a stage marked is_optional on the
    template it was snapshotted from, requires a reason."""
    step = get_project_step(db, project_id, step_id)
    if step.status != "Pending":
        raise ValidationAppError("Only a pending step can be waived.")
    if not step.is_optional:
        raise ValidationAppError("This step is not optional and cannot be waived.")
    if not reason.strip():
        raise ValidationAppError("A reason is required to waive a step.")

    incomplete_before = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number < step.sequence_number,
            ProjectApprovalStep.status == "Pending",
        )
        .count()
    )
    if incomplete_before > 0:
        raise ValidationAppError(
            "Steps must be resolved in order -- finish the steps before this one first."
        )

    step.status = "Waived"
    step.waived_at = datetime.now(timezone.utc)
    step.waived_by = user_id
    step.waived_reason = reason.strip()
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Approval process step waived: {step.name}", user_id, reason=reason.strip()
    )
    db.commit()
    db.refresh(step)
    return step


def unwaive_step(db: Session, project_id: int, step_id: int, user_id: int | None) -> ProjectApprovalStep:
    """Reverses a waive back to Pending -- same "only the most recently
    resolved step" rule as uncomplete_step."""
    step = get_project_step(db, project_id, step_id)
    if step.status != "Waived":
        return step

    later_resolved = (
        db.query(ProjectApprovalStep)
        .filter(
            ProjectApprovalStep.project_id == project_id,
            ProjectApprovalStep.sequence_number > step.sequence_number,
            ProjectApprovalStep.status != "Pending",
        )
        .count()
    )
    if later_resolved > 0:
        raise ValidationAppError(
            "Only the most recently completed or waived step can be undone -- undo later steps first."
        )

    step.status = "Pending"
    step.waived_at = None
    step.waived_by = None
    step.waived_reason = None
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Approval process step un-waived: {step.name}", user_id
    )
    db.commit()
    db.refresh(step)
    return step
