from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.workflow import WorkflowStage, WorkflowTemplate
from app.services import audit_service

ENTITY_TYPE = "WORKFLOW_TEMPLATE"

# The default project workflow, mirroring the canonical stage order used
# by PROJECT_STAGE_ALLOWED_TRANSITIONS (app/core/status_transitions.py).
# "Correction" is a loopback from Review rather than a forward stage, so
# it's intentionally left out of this linear seed list.
DEFAULT_TEMPLATE_NAME = "Standard Project Workflow"
DEFAULT_STAGES = [
    ("Enquiry", "Initial client enquiry is logged and qualified."),
    ("Quotation", "A quotation is prepared and sent to the client."),
    ("Contract", "The contract is drafted, negotiated and signed."),
    ("Design", "Design work is carried out for the project."),
    ("Government Submission", "Drawings and forms are submitted to the relevant authority."),
    ("Review", "The submission is under authority or internal review."),
    ("Approval", "The project has received approval and moves to execution."),
    ("Completed", "The project is complete."),
]


def _ensure_seeded(db: Session) -> None:
    """Creates a default template with the canonical project stages the
    first time this is called against an empty table, so the admin
    workflow page always has something to show and edit rather than being
    permanently stuck on an empty state with no way to create a template
    from the UI."""
    if db.query(WorkflowTemplate).filter(WorkflowTemplate.deleted_at.is_(None)).first() is not None:
        return
    template = WorkflowTemplate(name=DEFAULT_TEMPLATE_NAME, is_default=True)
    db.add(template)
    db.flush()
    for index, (name, description) in enumerate(DEFAULT_STAGES, start=1):
        db.add(WorkflowStage(template_id=template.id, name=name, description=description, sequence_number=index))
    db.commit()


def list_templates(db: Session) -> list[WorkflowTemplate]:
    _ensure_seeded(db)
    return (
        db.query(WorkflowTemplate)
        .filter(WorkflowTemplate.deleted_at.is_(None))
        .options(joinedload(WorkflowTemplate.stages))
        .order_by(WorkflowTemplate.id.asc())
        .all()
    )


def parse_template_id(raw: str) -> int:
    text = raw.removeprefix("WFT-") if raw.upper().startswith("WFT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid workflow template id.")
    return int(text)


def parse_stage_id(raw: str) -> int:
    text = raw.removeprefix("STG-") if raw.upper().startswith("STG-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid workflow stage id.")
    return int(text)


def get_template(db: Session, raw_id: str) -> WorkflowTemplate:
    template = (
        db.query(WorkflowTemplate)
        .filter(WorkflowTemplate.id == parse_template_id(raw_id), WorkflowTemplate.deleted_at.is_(None))
        .options(joinedload(WorkflowTemplate.stages))
        .first()
    )
    if not template:
        raise NotFoundError("Workflow template")
    return template


def get_stage(db: Session, raw_id: str) -> WorkflowStage:
    stage = db.query(WorkflowStage).filter(WorkflowStage.id == parse_stage_id(raw_id)).first()
    if not stage:
        raise NotFoundError("Workflow stage")
    return stage


def add_stage(db: Session, template_raw_id: str, name: str, description: str | None, user_id: int) -> WorkflowStage:
    template = get_template(db, template_raw_id)
    next_sequence = (max((s.sequence_number for s in template.stages), default=0)) + 1
    stage = WorkflowStage(template_id=template.id, name=name, description=description, sequence_number=next_sequence)
    db.add(stage)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, "Stage added", user_id, new_value=name,
    )
    db.commit()
    db.refresh(stage)
    return stage


def update_stage(db: Session, stage_raw_id: str, name: str | None, description: str | None, user_id: int) -> WorkflowStage:
    stage = get_stage(db, stage_raw_id)
    previous_name = stage.name
    if name is not None:
        stage.name = name
    if description is not None:
        stage.description = description
    audit_service.log_event(
        db, ENTITY_TYPE, stage.template_id, "Stage updated", user_id,
        previous_value=previous_name, new_value=stage.name,
    )
    db.commit()
    db.refresh(stage)
    return stage


def remove_stage(db: Session, stage_raw_id: str, user_id: int) -> None:
    stage = get_stage(db, stage_raw_id)
    template_id = stage.template_id
    removed_name = stage.name
    db.delete(stage)
    db.flush()
    # Close the sequence-number gap so later moves/inserts stay contiguous.
    remaining = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.template_id == template_id)
        .order_by(WorkflowStage.sequence_number.asc())
        .all()
    )
    for index, remaining_stage in enumerate(remaining, start=1):
        remaining_stage.sequence_number = index
    audit_service.log_event(db, ENTITY_TYPE, template_id, "Stage removed", user_id, previous_value=removed_name)
    db.commit()


def move_stage(db: Session, stage_raw_id: str, direction: str, user_id: int) -> list[WorkflowStage]:
    stage = get_stage(db, stage_raw_id)
    stages = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.template_id == stage.template_id)
        .order_by(WorkflowStage.sequence_number.asc())
        .all()
    )
    index = next(i for i, s in enumerate(stages) if s.id == stage.id)
    target_index = index - 1 if direction == "up" else index + 1
    if target_index < 0 or target_index >= len(stages):
        raise ValidationAppError("Cannot move stage past the start or end of the workflow.")

    stages[index], stages[target_index] = stages[target_index], stages[index]
    for position, ordered_stage in enumerate(stages, start=1):
        ordered_stage.sequence_number = position
    audit_service.log_event(db, ENTITY_TYPE, stage.template_id, f"Stage moved {direction}", user_id, new_value=stage.name)
    db.commit()
    for ordered_stage in stages:
        db.refresh(ordered_stage)
    return stages


def set_default_template(db: Session, template_raw_id: str, user_id: int) -> list[WorkflowTemplate]:
    template = get_template(db, template_raw_id)
    templates = db.query(WorkflowTemplate).filter(WorkflowTemplate.deleted_at.is_(None)).all()
    for t in templates:
        t.is_default = t.id == template.id
    audit_service.log_event(db, ENTITY_TYPE, template.id, "Set as default workflow", user_id, new_value=template.name)
    db.commit()
    return list_templates(db)
