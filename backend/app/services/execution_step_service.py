"""The weighted execution-step checklist that replaces manually typed
project progress.

Three sides:
  - Admin (Administration:edit) manages named, reusable step sets --
    ExecutionStepSetTemplate rows (e.g. "Standard Process", "Commercial
    Fit-out") -- and, within each, its own ordered ExecutionStepTemplate
    rows, each with a weight_percentage that should sum to 100 across
    that one set.
  - Every project is assigned one step set at creation (Project.
    step_set_id) and gets its own independent copy of exactly that
    set's steps the moment it's created (see project_service.
    create_project) -- ProjectExecutionStep rows, snapshotted, not a
    live reference. Since migration 0022, each step carries its own
    free-standing 0-100 completion_percentage (set independently of
    every other step, no enforced order) and optional remarks;
    project.progress is the weight_percentage-weighted sum of every
    step's percentage, recomputed after every change here, never typed
    in by hand.
  - Staff can additionally add steps directly on one project beyond
    whatever its assigned set specifies (add_custom_project_step) --
    "freedom to add or reduce" on top of the admin-configured baseline,
    same as excluding a template-derived step is the "reduce" half.
"""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.execution_step import ExecutionStepSetTemplate, ExecutionStepTemplate, ProjectExecutionStep
from app.models.project import Project
from app.services import audit_service

ENTITY_TYPE = "EXECUTION_STEP_TEMPLATE"
STEP_SET_ENTITY_TYPE = "EXECUTION_STEP_SET"
PROJECT_ENTITY_TYPE = "PROJECT"

# Which of the 7 project workflow stages an execution activity is
# tagged to (see project.py's WORKFLOW_STAGES) -- only the first 5,
# since no activity is ever expected to belong to "Execution &
# Tracking" itself (that's the stage that tracks all of them at once,
# not one they're filed under) or "Completed" (an end state, not a
# stage work happens during). Not to be confused with the 5 Project
# Approval Process gates in approval_process.py -- those are separate,
# external sign-offs, not something an execution activity is filed
# under.
STAGE_KEYS = (
    "Requirement",
    "Quotation",
    "Contract",
    "Design",
    "Government Submission",
)

# The fixed set of real-world events a template step can be wired to --
# see try_auto_fill below. Not free text: a typo'd trigger_key would
# silently never fire, so admin picks from this list rather than typing
# one. Add a new entry here (and wherever the matching service actually
# calls try_auto_fill) before it can be assigned to a step.
TRIGGER_KEYS = (
    "quotation_created",
    "contract_created",
    "gate:documents_signed",
    "gate:mew_approval",
    "gate:architectural_approval",
    "gate:submit_baladia_kfd",
)


def parse_step_set_id(raw: str) -> int:
    text = raw.removeprefix("ESS-") if raw.upper().startswith("ESS-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid execution step set id.")
    return int(text)


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


def _normalize_trigger_key(trigger_key: str) -> str | None:
    """'' means "no trigger" (the Add-step form's default, and the
    explicit way an update PATCH clears one) -- never confused with a
    field the caller simply didn't include in this particular PATCH,
    which arrives as Python None and is left untouched by the callers
    below."""
    if trigger_key == "":
        return None
    if trigger_key not in TRIGGER_KEYS:
        raise ValidationAppError("Invalid trigger.")
    return trigger_key


# ---------------------------------------------------------------------------
# Admin: step sets
# ---------------------------------------------------------------------------


def list_step_sets(db: Session) -> list[ExecutionStepSetTemplate]:
    return (
        db.query(ExecutionStepSetTemplate)
        .filter(ExecutionStepSetTemplate.deleted_at.is_(None))
        .order_by(ExecutionStepSetTemplate.name.asc())
        .all()
    )


def get_step_set(db: Session, step_set_id: int) -> ExecutionStepSetTemplate:
    step_set = (
        db.query(ExecutionStepSetTemplate)
        .filter(ExecutionStepSetTemplate.id == step_set_id, ExecutionStepSetTemplate.deleted_at.is_(None))
        .first()
    )
    if step_set is None:
        raise NotFoundError("Execution step set")
    return step_set


def default_step_set_id(db: Session) -> int:
    """Falls back to the oldest surviving step set -- in practice the
    seeded "Standard Process" from migration 0049, which every install
    has from day one -- for a caller (an older client, or a project
    created without an explicit choice) that doesn't specify one."""
    step_set = (
        db.query(ExecutionStepSetTemplate)
        .filter(ExecutionStepSetTemplate.deleted_at.is_(None))
        .order_by(ExecutionStepSetTemplate.id.asc())
        .first()
    )
    if step_set is None:
        raise ValidationAppError("No execution step sets are configured. Contact an administrator.")
    return step_set.id


def create_step_set(db: Session, name: str, description: str | None, user_id: int | None) -> ExecutionStepSetTemplate:
    if not name.strip():
        raise ValidationAppError("Step set name is required.")
    step_set = ExecutionStepSetTemplate(name=name.strip(), description=(description or "").strip() or None)
    db.add(step_set)
    db.flush()
    audit_service.log_event(db, STEP_SET_ENTITY_TYPE, step_set.id, "Execution step set created", user_id, new_value=step_set.name)
    db.commit()
    db.refresh(step_set)
    return step_set


def update_step_set(
    db: Session, step_set_id: int, name: str | None, description: str | None, user_id: int | None
) -> ExecutionStepSetTemplate:
    step_set = get_step_set(db, step_set_id)
    if name is not None:
        if not name.strip():
            raise ValidationAppError("Step set name is required.")
        step_set.name = name.strip()
    if description is not None:
        step_set.description = description.strip() or None
    audit_service.log_event(db, STEP_SET_ENTITY_TYPE, step_set.id, "Execution step set updated", user_id)
    db.commit()
    db.refresh(step_set)
    return step_set


def delete_step_set(db: Session, step_set_id: int, user_id: int | None) -> None:
    step_set = get_step_set(db, step_set_id)
    in_use = db.query(Project).filter(Project.step_set_id == step_set_id, Project.deleted_at.is_(None)).count()
    if in_use > 0:
        raise ValidationAppError(
            f"{in_use} project(s) are currently assigned to this step set -- reassign or archive them first."
        )
    step_set.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(
        db, STEP_SET_ENTITY_TYPE, step_set.id, "Execution step set removed", user_id, previous_value=step_set.name
    )
    db.commit()


# ---------------------------------------------------------------------------
# Admin: template steps within one step set
# ---------------------------------------------------------------------------


def list_template(db: Session, step_set_id: int) -> list[ExecutionStepTemplate]:
    return (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.step_set_id == step_set_id, ExecutionStepTemplate.deleted_at.is_(None))
        .order_by(ExecutionStepTemplate.sequence_number.asc())
        .all()
    )


def template_total_weight(db: Session, step_set_id: int) -> float:
    return sum(float(s.weight_percentage) for s in list_template(db, step_set_id))


def create_template_step(
    db: Session,
    step_set_id: int,
    name: str,
    weight_percentage: float,
    stage_key: str,
    is_optional: bool,
    trigger_key: str,
    user_id: int | None,
) -> ExecutionStepTemplate:
    get_step_set(db, step_set_id)  # 404s if the set doesn't exist
    if not name.strip():
        raise ValidationAppError("Step name is required.")
    if weight_percentage <= 0:
        raise ValidationAppError("Weight must be greater than 0.")
    if stage_key not in STAGE_KEYS:
        raise ValidationAppError("Invalid stage.")

    max_sequence = (
        db.query(ExecutionStepTemplate)
        .filter(ExecutionStepTemplate.step_set_id == step_set_id, ExecutionStepTemplate.deleted_at.is_(None))
        .count()
    )
    step = ExecutionStepTemplate(
        step_set_id=step_set_id,
        name=name.strip(),
        sequence_number=max_sequence + 1,
        weight_percentage=weight_percentage,
        stage_key=stage_key,
        is_optional=is_optional,
        trigger_key=_normalize_trigger_key(trigger_key),
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
    trigger_key: str | None,
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
    if trigger_key is not None:
        step.trigger_key = _normalize_trigger_key(trigger_key)
    audit_service.log_event(db, ENTITY_TYPE, step.id, "Execution step updated", user_id)
    db.commit()
    db.refresh(step)
    return step


def delete_template_step(db: Session, step_id: int, user_id: int | None) -> None:
    step = get_template_step(db, step_id)
    step.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, step.id, "Execution step removed", user_id, previous_value=step.name)
    # Close the gap in sequence numbers so the remaining steps in this
    # same step set stay a clean, contiguous 1..N -- otherwise "move
    # up/down" (which swaps with the adjacent sequence_number) would
    # eventually stop working cleanly around a hole.
    remaining = (
        db.query(ExecutionStepTemplate)
        .filter(
            ExecutionStepTemplate.deleted_at.is_(None),
            ExecutionStepTemplate.step_set_id == step.step_set_id,
            ExecutionStepTemplate.sequence_number > step.sequence_number,
        )
        .order_by(ExecutionStepTemplate.sequence_number.asc())
        .all()
    )
    for s in remaining:
        s.sequence_number -= 1
    db.commit()


def move_template_step(db: Session, step_id: int, direction: str, user_id: int | None) -> list[ExecutionStepTemplate]:
    """direction: 'up' or 'down' -- swaps this step's sequence_number
    with its immediate neighbor in the same step set. Simple, safe
    reordering: no arbitrary "move to position N" that could produce a
    confusing intermediate state if two requests overlap."""
    if direction not in ("up", "down"):
        raise ValidationAppError("direction must be 'up' or 'down'.")
    step = get_template_step(db, step_id)
    neighbor_sequence = step.sequence_number - 1 if direction == "up" else step.sequence_number + 1
    neighbor = (
        db.query(ExecutionStepTemplate)
        .filter(
            ExecutionStepTemplate.deleted_at.is_(None),
            ExecutionStepTemplate.step_set_id == step.step_set_id,
            ExecutionStepTemplate.sequence_number == neighbor_sequence,
        )
        .first()
    )
    if neighbor is None:
        raise ValidationAppError(f"This step is already at the {'top' if direction == 'up' else 'bottom'}.")
    step.sequence_number, neighbor.sequence_number = neighbor.sequence_number, step.sequence_number
    audit_service.log_event(db, ENTITY_TYPE, step.id, f"Execution step moved {direction}", user_id)
    db.commit()
    return list_template(db, step.step_set_id)


# ---------------------------------------------------------------------------
# Per-project checklist
# ---------------------------------------------------------------------------


def snapshot_steps_for_project(db: Session, project_id: int) -> None:
    """Called once, at project creation (project_service.create_project,
    which has already resolved and set project.step_set_id before
    calling this) -- copies that one step set's current template into
    this project's own rows. Does not commit; the caller's own
    transaction covers this too, same convention as timeline_service.
    create_system_event."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        return
    step_set_id = project.step_set_id if project.step_set_id is not None else default_step_set_id(db)
    for template_step in list_template(db, step_set_id):
        db.add(
            ProjectExecutionStep(
                project_id=project_id,
                name=template_step.name,
                sequence_number=template_step.sequence_number,
                weight_percentage=template_step.weight_percentage,
                stage_key=template_step.stage_key,
                is_optional=template_step.is_optional,
                trigger_key=template_step.trigger_key,
                is_custom=False,
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


def included_steps(steps: list[ProjectExecutionStep]) -> list[ProjectExecutionStep]:
    """Steps that count toward %complete and the Completed-stage gate --
    everything except what this specific project has excluded (see
    ProjectExecutionStep.is_excluded)."""
    return [s for s in steps if not s.is_excluded]


def compute_weighted_completion(db: Session, project_id: int) -> int:
    """The weight_percentage-weighted sum of every included step's own
    completion_percentage, renormalized against the included weight
    total -- pure calculation, no write. Used both as the fractional
    fill for the "Execution & Tracking" band of project_service.
    recompute_progress (the sole writer of project.progress) and,
    before this checklist was folded into that stage-driven number, as
    the entirety of project.progress itself."""
    steps = included_steps(list_project_steps(db, project_id))
    total_weight = sum(float(s.weight_percentage) for s in steps)
    if total_weight <= 0:
        return 0
    # Renormalized against only the included weight, so excluding a
    # step never drags %complete down for work that was never
    # applicable to this project -- the remaining steps still scale
    # to a full 0-100.
    weighted = sum(float(s.weight_percentage) * s.completion_percentage / 100 for s in steps)
    return max(0, min(100, round(weighted / total_weight * 100)))


def _recompute_progress(db: Session, project_id: int) -> Project | None:
    """Recomputes and persists project.progress -- delegates to
    project_service.recompute_progress (a local import to avoid a
    circular import: project_service already imports this module at
    module level, see audit_service.get_history for the same pattern)
    since that's now the single place project.progress is written, so a
    checklist update moves the right fractional amount within whichever
    stage band the project is actually in instead of overwriting it
    with the checklist percentage alone. Returns the project (or None if
    it's gone) so callers can also try an auto stage-advance with it."""
    from app.services import project_service

    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        return None
    project_service.recompute_progress(db, project)
    return project


# Several execution steps duplicate a real-world fact the app already
# tracks somewhere else entirely -- e.g. "Quotation prepared" is just
# the existence of a Quotation record (quotation_service.
# create_quotation), and "MEW approval request submitted" is one of the
# 5 Project Approval Process gates (approval_process_service, stage_key
# "mew_approval") staff already close independently. Rather than making
# staff tick the same fact twice, the service that just made it true
# calls try_auto_fill below, which looks a project's own snapshot row
# up directly by trigger_key -- not by a hardcoded sequence-number table
# (migration 0049 retired that: it could only ever describe one fixed
# step order, which breaks the moment a second step set exists with its
# own numbering).
#
# Every trigger here is a conservative, one-directional inference ("if
# the trigger fired, this step is *at least* as done as it claims") --
# never a fabricated guess. A step with no trigger_key at all (the
# majority -- actual design/drawing production work) has no other
# system tracking it and stays a manual checklist entry; there's
# nothing to auto-fill it from without inventing progress that hasn't
# genuinely happened.
def try_auto_fill(db: Session, project_id: int, trigger: str, user_id: int | None) -> None:
    """Auto-completes the one execution step (if any) on this project
    whose trigger_key matches `trigger`. Sets completion_percentage to
    100 only if it's currently lower (never overrides a value staff
    already pushed higher or lower it back down) and only if the step
    isn't excluded from this project; sets a short default remark only
    if remarks is currently empty, so it never clobbers a staff-written
    note. Staff can still edit the percentage afterward exactly like any
    other step -- this sets a sensible default the moment the real fact
    becomes known, it doesn't lock anything. Silently does nothing if no
    step on this project maps to this trigger, or the matching step is
    excluded or already at 100%."""
    step = (
        db.query(ProjectExecutionStep)
        .filter(ProjectExecutionStep.project_id == project_id, ProjectExecutionStep.trigger_key == trigger)
        .first()
    )
    if step is None or step.is_excluded or step.completion_percentage >= 100:
        return

    step.completion_percentage = 100
    if not (step.remarks or "").strip():
        step.remarks = "Auto-completed -- tracked automatically elsewhere in the project."
    audit_service.log_event(
        db, PROJECT_ENTITY_TYPE, project_id, f"Execution step auto-completed: {step.name}", user_id,
        new_value="100%",
    )
    _recompute_progress(db, project_id)


# Companion to try_auto_fill above, but coarser: rather than one
# specific real-world fact per step, this closes out *every* step whose
# stage_key belongs to a workflow stage the project has already moved
# past entirely. A project can't reach "Design" without "Contract"
# having already cleared its own exit criteria (see
# _assert_stage_exit_criteria), so by the time the project is sitting
# in a later stage, every step tagged to an earlier one is -- at
# minimum -- as good as done; there's no reason to make staff tick
# every box by hand for stages that are already firmly in the past just
# because no single specific trigger above happened to cover them.
#
# Same conservative rule as try_auto_fill: only ever raises a step's
# completion_percentage, never lowers one staff already set, and never
# touches a step the project has excluded (is_excluded) or already
# marked complete.
def auto_fill_steps_for_passed_stages(db: Session, project_id: int, current_stage: str, user_id: int | None) -> None:
    from app.models.project import WORKFLOW_STAGES

    if current_stage not in WORKFLOW_STAGES:
        return
    current_index = WORKFLOW_STAGES.index(current_stage)
    # Every STAGE_KEYS entry strictly before the project's current
    # stage is "passed"; STAGE_KEYS only covers the first 5 workflow
    # stages (see its own docstring above), so this naturally excludes
    # "Execution & Tracking" and "Completed" from ever being treated as
    # a passed *prerequisite* stage for another step.
    passed_stages = {stage for stage in STAGE_KEYS if WORKFLOW_STAGES.index(stage) < current_index}
    if not passed_stages:
        return

    steps = list_project_steps(db, project_id)
    changed_names: list[str] = []
    for step in steps:
        if step.is_excluded or step.completion_percentage >= 100:
            continue
        if step.stage_key not in passed_stages:
            continue
        step.completion_percentage = 100
        if not (step.remarks or "").strip():
            step.remarks = f"Auto-completed -- the project has already moved past the '{step.stage_key}' stage."
        changed_names.append(step.name)

    if changed_names:
        audit_service.log_event(
            db, PROJECT_ENTITY_TYPE, project_id,
            "Execution steps auto-completed for passed stages", user_id,
            new_value=f"{len(changed_names)} activities: {', '.join(changed_names)}",
        )
        _recompute_progress(db, project_id)


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
    project = _recompute_progress(db, project_id)
    if project is not None:
        from app.services import project_service

        # The session is autoflush=False -- flush first so the exit-
        # criteria check's own fresh query over every execution step
        # actually sees this step's new completion_percentage rather
        # than the pre-change value still on file.
        db.flush()
        project_service.try_auto_advance_stage(db, project, user_id)
    db.commit()
    db.refresh(step)
    return step


def bulk_set_steps(
    db: Session,
    project_id: int,
    items: list,
    user_id: int | None,
) -> list[ProjectExecutionStep]:
    """The checklist's single Save button -- every changed row
    (percentage, remarks, excluded/reason) lands in one transaction and
    one audit entry instead of one PATCH call per row. `items` is a
    list of (parsed int id, ExecutionStepBulkItem) pairs."""
    changed_names: list[str] = []
    for parsed_id, item in items:
        step = get_project_step(db, project_id, parsed_id)
        if (
            step.completion_percentage != item.completionPercentage
            or (step.remarks or None) != ((item.remarks or "").strip() or None)
            or step.is_excluded != item.isExcluded
            or (step.excluded_reason or None) != ((item.excludedReason or "").strip() or None)
        ):
            changed_names.append(step.name)
        step.completion_percentage = item.completionPercentage
        step.remarks = (item.remarks or "").strip() or None
        step.is_excluded = item.isExcluded
        step.excluded_reason = (item.excludedReason or "").strip() or None if item.isExcluded else None

    if changed_names:
        audit_service.log_event(
            db, PROJECT_ENTITY_TYPE, project_id,
            "Execution checklist saved", user_id,
            new_value=f"{len(changed_names)} activities updated: {', '.join(changed_names)}",
        )
    project = _recompute_progress(db, project_id)
    if project is not None:
        from app.services import project_service

        # Same autoflush=False reasoning as save_step_progress above.
        db.flush()
        project_service.try_auto_advance_stage(db, project, user_id)
    db.commit()
    return list_project_steps(db, project_id)


def add_custom_project_step(
    db: Session, project_id: int, name: str, weight_percentage: float, stage_key: str, user_id: int | None
) -> ProjectExecutionStep:
    """Staff's own "freedom to add" beyond whatever the project's
    assigned step set specified -- the complement of excluding a
    template-derived step (the "reduce" half of the same freedom).
    Appended after every existing row regardless of stage_key -- there's
    no reordering UI for project-level steps, unlike the admin template
    editor."""
    if not name.strip():
        raise ValidationAppError("Step name is required.")
    if weight_percentage <= 0:
        raise ValidationAppError("Weight must be greater than 0.")
    if stage_key not in STAGE_KEYS:
        raise ValidationAppError("Invalid stage.")

    max_sequence = (
        db.query(func.max(ProjectExecutionStep.sequence_number))
        .filter(ProjectExecutionStep.project_id == project_id)
        .scalar()
        or 0
    )
    step = ProjectExecutionStep(
        project_id=project_id,
        name=name.strip(),
        sequence_number=max_sequence + 1,
        weight_percentage=weight_percentage,
        stage_key=stage_key,
        is_optional=False,
        trigger_key=None,
        is_custom=True,
        completion_percentage=0,
    )
    db.add(step)
    db.flush()
    audit_service.log_event(
        db, PROJECT_ENTITY_TYPE, project_id, f"Execution step added: {step.name}", user_id, new_value=step.name
    )
    _recompute_progress(db, project_id)
    db.commit()
    db.refresh(step)
    return step


def delete_custom_project_step(db: Session, project_id: int, step_id: int, user_id: int | None) -> None:
    """Only a custom, project-added step (is_custom) can be deleted
    outright -- a template-derived step can only ever be excluded (see
    ProjectExecutionStep.is_excluded's own docstring), so the project's
    history stays an honest reflection of what its assigned step set
    actually specified."""
    step = get_project_step(db, project_id, step_id)
    if not step.is_custom:
        raise ValidationAppError("Only a custom step can be deleted -- exclude a template step instead.")
    name = step.name
    db.delete(step)
    audit_service.log_event(db, PROJECT_ENTITY_TYPE, project_id, f"Execution step removed: {name}", user_id, previous_value=name)
    db.flush()
    _recompute_progress(db, project_id)
    db.commit()
