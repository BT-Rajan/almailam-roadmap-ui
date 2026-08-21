"""The weighted execution-step checklist that replaces manually typed
project progress.

Two sides:
  - Admin (Administration:edit) manages the master template --
    ExecutionStepTemplate rows, ordered, each with a weight_percentage.
  - Every project gets its own independent copy of that template the
    moment it's created (see project_service.create_project) --
    ProjectExecutionStep rows, snapshotted, not a live reference. Since
    migration 0022, each step carries its own free-standing 0-100
    completion_percentage (set independently of every other step, no
    enforced order) and optional remarks; project.progress is the
    weight_percentage-weighted sum of every step's percentage,
    recomputed after every change here, never typed in by hand.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.execution_step import ExecutionStepTemplate, ProjectExecutionStep
from app.models.project import Project
from app.services import audit_service

ENTITY_TYPE = "EXECUTION_STEP_TEMPLATE"
PROJECT_ENTITY_TYPE = "PROJECT"

# The 5 Project Approval Process stages every execution step is grouped
# under (see approval_process.py) -- kept here, not re-derived from the
# DB, since it's the same fixed list the approval_process_templates seed
# uses and nothing about it is meant to be admin-editable.
STAGE_KEYS = (
    "documents_signed",
    "mew_approval",
    "architectural_approval",
    "submit_baladia_kfd",
    "permit_approved",
)


def parse_template_step_id(raw: str) -> int:
    text = raw.removeprefix("EST-") if raw.upper().startswith("EST-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid execution step id.")
    return int(text)


def parse_project_step_id(raw: str) -> int:
    text = raw.removeprefix("PES-") if raw.upper().startswith("PES-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid project execution step id.")
    return int(text)


# ---------------------------------------------------------------------------
# Admin template management
# ---------------------------------------------------------------------------


def list_template(db: Session) -> list[ExecutionStepTemplate]:
    return (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.deleted_at.is_(None))
        .order_by(ExecutionStepTemplate.sequence_number.asc())
        .all()
    )


def template_total_weight(db: Session) -> float:
    return sum(float(s.weight_percentage) for s in list_template(db))


def create_template_step(
    db: Session,
    name: str,
    weight_percentage: float,
    stage_key: str,
    is_optional: bool,
    user_id: int | None,
) -> ExecutionStepTemplate:
    if not name.strip():
        raise ValidationAppError("Step name is required.")
    if weight_percentage <= 0:
        raise ValidationAppError("Weight must be greater than 0.")
    if stage_key not in STAGE_KEYS:
        raise ValidationAppError("Invalid stage.")

    max_sequence = db.query(ExecutionStepTemplate).filter(ExecutionStepTemplate.deleted_at.is_(None)).count()
    step = ExecutionStepTemplate(
        name=name.strip(),
        sequence_number=max_sequence + 1,
        weight_percentage=weight_percentage,
        stage_key=stage_key,
        is_optional=is_optional,
    )
    db.add(step)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, step.id, "Execution step created", user_id, new_value=step.name)
    db.commit()
    db.refresh(step)
    return step


def get_template_step(db: Session, step_id: int) -> ExecutionStepTemplate:
    step = (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.id == step_id, ExecutionStepTemplate.deleted_at.is_(None))
        .first()
    )
    if step is None:
        raise NotFoundError("Execution step")
    return step


def update_template_step(
    db: Session,
    step_id: int,
    name: str | None,
    weight_percentage: float | None,
    stage_key: str | None,
    is_optional: bool | None,
    user_id: int | None,
) -> ExecutionStepTemplate:
    step = get_template_step(db, step_id)
    if name is not None:
        if not name.strip():
            raise ValidationAppError("Step name is required.")
        step.name = name.strip()
    if weight_percentage is not None:
        if weight_percentage <= 0:
            raise ValidationAppError("Weight must be greater than 0.")
        step.weight_percentage = weight_percentage
    if stage_key is not None:
        if stage_key not in STAGE_KEYS:
            raise ValidationAppError("Invalid stage.")
        step.stage_key = stage_key
    if is_optional is not None:
        step.is_optional = is_optional
    audit_service.log_event(db, ENTITY_TYPE, step.id, "Execution step updated", user_id)
    db.commit()
    db.refresh(step)
    return step


def delete_template_step(db: Session, step_id: int, user_id: int | None) -> None:
    step = get_template_step(db, step_id)
    step.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, step.id, "Execution step removed", user_id, previous_value=step.name)
    # Close the gap in sequence numbers so the remaining steps stay a
    # clean, contiguous 1..N -- otherwise "move up/down" (which swaps
    # with the adjacent sequence_number) would eventually stop working
    # cleanly around a hole.
    remaining = (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.deleted_at.is_(None), ExecutionStepTemplate.sequence_number > step.sequence_number)
        .order_by(ExecutionStepTemplate.sequence_number.asc())
        .all()
    )
    for s in remaining:
        s.sequence_number -= 1
    db.commit()


def move_template_step(db: Session, step_id: int, direction: str, user_id: int | None) -> list[ExecutionStepTemplate]:
    """direction: 'up' or 'down' -- swaps this step's sequence_number
    with its immediate neighbor. Simple, safe reordering: no arbitrary
    "move to position N" that could produce a confusing intermediate
    state if two requests overlap."""
    if direction not in ("up", "down"):
        raise ValidationAppError("direction must be 'up' or 'down'.")
    step = get_template_step(db, step_id)
    neighbor_sequence = step.sequence_number - 1 if direction == "up" else step.sequence_number + 1
    neighbor = (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.deleted_at.is_(None), ExecutionStepTemplate.sequence_number == neighbor_sequence)
        .first()
    )
    if neighbor is None:
        raise ValidationAppError(f"This step is already at the {'top' if direction == 'up' else 'bottom'}.")
    step.sequence_number, neighbor.sequence_number = neighbor.sequence_number, step.sequence_number
    audit_service.log_event(db, ENTITY_TYPE, step.id, f"Execution step moved {direction}", user_id)
    db.commit()
    return list_template(db)


# ---------------------------------------------------------------------------
# Per-project checklist
# ---------------------------------------------------------------------------


def snapshot_steps_for_project(db: Session, project_id: int) -> None:
    """Called once, at project creation (project_service.create_project)
    -- copies the current template into this project's own rows. Does
    not commit; the caller's own transaction covers this too, same
    convention as timeline_service.create_system_event."""
    for template_step in list_template(db):
        db.add(
            ProjectExecutionStep(
                project_id=project_id,
                name=template_step.name,
                sequence_number=template_step.sequence_number,
                weight_percentage=template_step.weight_percentage,
                stage_key=template_step.stage_key,
                is_optional=template_step.is_optional,
                completion_percentage=0,
            )
        )


def list_project_steps(db: Session, project_id: int) -> list[ProjectExecutionStep]:
    return (
        db.query(ProjectExecutionStep)
        .filter(ProjectExecutionStep.project_id == project_id)
        .order_by(ProjectExecutionStep.sequence_number.asc())
        .all()
    )


def _recompute_progress(db: Session, project_id: int) -> int:
    steps = list_project_steps(db, project_id)
    total = sum(float(s.weight_percentage) * s.completion_percentage / 100 for s in steps)
    # project.progress is a bounded SMALLINT percentage -- clamp defends
    # against a template that doesn't sum to exactly 100 (admin is free
    # to leave it under- or over-100 temporarily while tuning weights)
    # ever producing a nonsensical stored value.
    progress = max(0, min(100, round(total)))
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.progress = progress
    return progress


def get_project_step(db: Session, project_id: int, step_id: int) -> ProjectExecutionStep:
    step = (
        db.query(ProjectExecutionStep)
        .filter(ProjectExecutionStep.id == step_id, ProjectExecutionStep.project_id == project_id)
        .first()
    )
    if step is None:
        raise NotFoundError("Project execution step")
    return step


def set_step_progress(
    db: Session, project_id: int, step_id: int, completion_percentage: int, remarks: str | None, user_id: int | None
) -> ProjectExecutionStep:
    """Sets one step's completion percentage (and optional remarks)
    independently of every other step -- no order enforced, no linear
    lock. A quick-mark button (20/40/60/80/100) and a manual number
    entry both land here identically."""
    if not 0 <= completion_percentage <= 100:
        raise ValidationAppError("Completion percentage must be between 0 and 100.")

    step = get_project_step(db, project_id, step_id)
    step.completion_percentage = completion_percentage
    step.remarks = (remarks or "").strip() or None
    audit_service.log_event(
        db, PROJECT_ENTITY_TYPE, project_id,
        f"Execution step progress updated: {step.name}", user_id,
        new_value=f"{completion_percentage}%",
    )
    _recompute_progress(db, project_id)
    db.commit()
    db.refresh(step)
    return step
