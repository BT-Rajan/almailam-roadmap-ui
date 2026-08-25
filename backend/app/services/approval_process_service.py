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
from app.models.document import ProjectDocument
from app.models.project import Project
from app.services import audit_service, execution_step_service

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


def is_stage_gate_complete(db: Session, project_id: int, stage_key: str) -> bool:
    """A stage gate closes via either of two independent paths (migration
    0033) -- its own review document uploaded (storage_key set), or every
    project_documents row tagged to it approved and confirmed
    (completed_at set). Matches ProjectApprovalStepOut.isComplete exactly
    -- the one place this OR condition should be written, since checking
    only storage_key (as project_service._assert_stage_exit_criteria did
    before this helper existed) silently ignores the second path
    entirely, blocking a project that's genuinely eligible to advance."""
    gate = get_project_step_by_stage(db, project_id, stage_key)
    return gate.storage_key is not None or gate.completed_at is not None


def _try_auto_advance_project_stage(db: Session, project_id: int, user_id: int | None) -> None:
    """Closing the last of the 4 approval gates required to leave
    "Design"/"Government Submission" (see project_service.
    _assert_stage_exit_criteria) is exactly what lets a project converge
    into "Execution & Tracking" -- advance it automatically instead of
    requiring a separate manual stage click once that's already true.
    Local import: project_service already imports this module at module
    level, so importing it back at module level here would be circular
    (see audit_service.get_history for the same pattern)."""
    from app.services import project_service

    # The session is autoflush=False -- without this, a stage gate's own
    # storage_key/completed_at change made earlier in this same
    # transaction wouldn't be visible yet to the fresh DB query
    # is_stage_gate_complete() runs as part of _assert_stage_exit_
    # criteria, so the check would silently see stale (pre-change) data
    # and never actually advance.
    db.flush()
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is not None:
        project_service.try_auto_advance_stage(db, project, user_id)


def upload_stage_gate_document(
    db: Session, project_id: int, stage_key: str, file: UploadFile, user_id: int | None
) -> ProjectApprovalStep:
    """Uploading a stage's review document IS what marks that stage
    complete -- there is no separate "mark complete" action. Uploading
    again replaces the previous file (the old storage_key is simply
    overwritten; nothing keeps the superseded file around, this is a
    single current gate document, not a version history).

    The 5-stage approval process and the 23-activity execution checklist
    are independent tracks that both run against the project at the same
    time -- a stage's gate document can be uploaded whether or not any
    particular execution activity is finished, so there is deliberately
    no check against ProjectExecutionStep completion here. (An earlier
    version of this function blocked the upload until every execution
    step sharing this stage_key hit 100%, on the assumption that the
    activities were partitioned one-to-one under a stage; they aren't.)"""
    step = get_project_step_by_stage(db, project_id, stage_key)

    storage_key, original_filename, size_bytes = save_upload(file, "stage-gates")
    step.storage_key = storage_key
    step.original_filename = original_filename
    step.file_size_bytes = size_bytes
    step.uploaded_at = datetime.now(timezone.utc)
    step.uploaded_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, project_id, f"Stage gate document uploaded: {step.name}", user_id, new_value=original_filename
    )
    _try_auto_advance_project_stage(db, project_id, user_id)
    # One-directional only, unlike the removed blocking check this
    # function's own docstring mentions above: closing this gate can
    # auto-complete the one execution step that duplicates it (see
    # execution_step_service._AUTO_FILL_TRIGGERS), but an execution
    # step's own completion never gates or auto-closes a stage gate.
    execution_step_service.try_auto_fill(db, project_id, f"gate:{stage_key}", user_id)
    db.commit()
    db.refresh(step)
    return step


def complete_stage_from_documents(db: Session, project_id: int, stage_key: str, user_id: int | None) -> ProjectApprovalStep:
    """Second, independent way to close a stage gate: instead of
    uploading a review document, the tagged design documents
    (project_documents.stage_key == this stage_key) are approved and
    a user confirms. Re-validated here, not just trusted from the
    frontend's own count -- requires at least one tagged document,
    doesn't require every one to be Approved (a stage can still be
    confirmed complete with some Rejected/Under Review, same as the
    frontend's "either way, confirm" flow), but does refuse an empty
    tag set outright since there'd be nothing to have approved.
    Calling this again just re-stamps completed_at/completed_by --
    idempotent, no separate "already complete" error."""
    step = get_project_step_by_stage(db, project_id, stage_key)

    tagged_documents = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.stage_key == stage_key,
            ProjectDocument.deleted_at.is_(None),
        )
        .all()
    )
    if not tagged_documents:
        raise ValidationAppError("No documents are tagged to this stage yet.")

    approved_count = sum(1 for d in tagged_documents if d.status == "Approved")

    step.completed_at = datetime.now(timezone.utc)
    step.completed_by = user_id
    audit_service.log_event(
        db,
        ENTITY_TYPE,
        project_id,
        f"Stage marked complete from document approvals: {step.name} "
        f"({approved_count}/{len(tagged_documents)} documents approved)",
        user_id,
    )
    _try_auto_advance_project_stage(db, project_id, user_id)
    execution_step_service.try_auto_fill(db, project_id, f"gate:{stage_key}", user_id)
    db.commit()
    db.refresh(step)
    return step


def get_stage_gate_download_target(db: Session, project_id: int, stage_key: str):
    step = get_project_step_by_stage(db, project_id, stage_key)
    if not step.storage_key:
        raise NotFoundError("Stage gate document")
    return resolve_path(step.storage_key), step.original_filename
