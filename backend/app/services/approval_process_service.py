"""The 5-stage Project Approval Process, built as a separate, self-
contained trial -- not touching current_stage or
PROJECT_STAGE_ALLOWED_TRANSITIONS in any way. See approval_process.py's
own docstring for the full reasoning.

Since migration 0022, each of the 5 stages is a stage gate: uploading
its review document is what marks it complete (see
upload_stage_gate_document below), not a separate manual action.
"""

from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.models.approval_process import ApprovalProcessTemplate, ProjectApprovalStep
from app.models.execution_step import ProjectExecutionStep
from app.services import audit_service

ENTITY_TYPE = "PROJECT"


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
            )
        )


def list_project_steps(db: Session, project_id: int) -> list[ProjectApprovalStep]:
    return (
        db.query(ProjectApprovalStep)
        .filter(ProjectApprovalStep.project_id == project_id)
        .order_by(ProjectApprovalStep.sequence_number.asc())
        .all()
    )


def get_project_step_by_stage(db: Session, project_id: int, stage_key: str) -> ProjectApprovalStep:
    step = (
        db.query(ProjectApprovalStep)
        .filter(ProjectApprovalStep.project_id == project_id, ProjectApprovalStep.stage_key == stage_key)
        .first()
    )
    if step is None:
        raise NotFoundError("Approval process stage")
    return step


def _pending_execution_steps_count(db: Session, project_id: int, stage_key: str) -> int:
    """How many of this project's execution steps (see execution_step.py)
    are tagged to this approval stage and still below 100% completion.
    The 23-step checklist and the 5-stage approval process are otherwise
    independent tracks that only share stage_key for display grouping
    (see ProjectProcessTab.vue's accordion) -- without this check, a
    stage's gate document could be uploaded (closing it out) while the
    execution steps grouped visually underneath it are still sitting
    unfinished, which reads as a flat contradiction in that same
    accordion."""
    return (
        db.query(ProjectExecutionStep)
        .filter(
            ProjectExecutionStep.project_id == project_id,
            ProjectExecutionStep.stage_key == stage_key,
            ProjectExecutionStep.completion_percentage < 100,
        )
        .count()
    )


def upload_stage_gate_document(
    db: Session, project_id: int, stage_key: str, file: UploadFile, user_id: int | None
) -> ProjectApprovalStep:
    """Uploading a stage's review document IS what marks that stage
    complete -- there is no separate "mark complete" action. Uploading
    again replaces the previous file (the old storage_key is simply
    overwritten; nothing keeps the superseded file around, this is a
    single current gate document, not a version history)."""
    step = get_project_step_by_stage(db, project_id, stage_key)

    pending_steps = _pending_execution_steps_count(db, project_id, stage_key)
    if pending_steps > 0:
        raise ValidationAppError(
            f"{pending_steps} execution step(s) for this stage are still below 100% -- "
            "finish them before uploading this stage's gate document."
        )

    storage_key, original_filename, size_bytes = save_upload(file, "stage-gates")
    step.storage_key = storage_key
    step.original_filename = original_filename
    step.file_size_bytes = size_bytes
    step.uploaded_at = datetime.now(timezone.utc)
    step.uploaded_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Stage gate document uploaded: {step.name}", user_id, new_value=original_filename
    )
    db.commit()
    db.refresh(step)
    return step


def get_stage_gate_download_target(db: Session, project_id: int, stage_key: str):
    step = get_project_step_by_stage(db, project_id, stage_key)
    if not step.storage_key:
        raise NotFoundError("Stage gate document")
    return resolve_path(step.storage_key), step.original_filename
