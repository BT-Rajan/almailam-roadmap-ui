"""Admin-defined, reusable document reference list per Design/Permit/
Supervision catalog activity (migration 0073) -- "we might be using a
single document for more than one activity, we can reuse that
document." DocumentRequirement/DocumentRequirementLink are still purely
catalog-level and informational on their own; what actually gates
anything is ProjectDocumentRequirementFulfillment below (#4/#5 on the
Design-stage tangle pass) -- the per-project checkbox state answering
"has THIS project's copy of this activity/permit actually produced
this document", which close_design_activity/set_permit_status/
set_supervision_status and the Handover exit criterion both check
before letting the corresponding item close (see
assert_checklist_fulfilled/list_outstanding_checklist_items below)."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.document_requirement import DocumentRequirement, DocumentRequirementLink, ProjectDocumentRequirementFulfillment
from app.models.project import Project
from app.services import audit_service, permit_catalog_service, service_catalog_service

ENTITY_TYPE = "DOCUMENT_REQUIREMENT"


def _requirements_query(db: Session):
    return db.query(DocumentRequirement).filter(DocumentRequirement.deleted_at.is_(None))


def list_requirements(db: Session) -> list[DocumentRequirement]:
    return _requirements_query(db).order_by(DocumentRequirement.name.asc()).all()


def parse_requirement_id(raw: str) -> int:
    if not raw.isdigit():
        raise ValidationAppError("Invalid document requirement id.")
    return int(raw)


def get_requirement(db: Session, raw_id: str) -> DocumentRequirement:
    requirement = _requirements_query(db).filter(DocumentRequirement.id == parse_requirement_id(raw_id)).first()
    if requirement is None:
        raise NotFoundError("Document requirement")
    return requirement


def _assert_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    query = db.query(DocumentRequirement).filter(
        DocumentRequirement.deleted_at.is_(None), func.lower(DocumentRequirement.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        query = query.filter(DocumentRequirement.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(f'A document requirement named "{name.strip()}" already exists.')


def create_requirement(db: Session, name: str, description: str | None, user_id: int) -> DocumentRequirement:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Document requirement name is required.")
    _assert_name_available(db, clean_name)
    requirement = DocumentRequirement(name=clean_name, description=(description or "").strip() or None)
    db.add(requirement)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, requirement.id, "Document requirement added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(requirement)
    return requirement


def update_requirement(
    db: Session, raw_id: str, name: str | None, description: str | None, user_id: int
) -> DocumentRequirement:
    requirement = get_requirement(db, raw_id)
    previous_name = requirement.name
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationAppError("Document requirement name is required.")
        _assert_name_available(db, clean_name, exclude_id=requirement.id)
        requirement.name = clean_name
    if description is not None:
        requirement.description = description.strip() or None
    audit_service.log_event(
        db, ENTITY_TYPE, requirement.id, "Document requirement updated", user_id,
        previous_value=previous_name, new_value=requirement.name,
    )
    db.commit()
    db.refresh(requirement)
    return requirement


def remove_requirement(db: Session, raw_id: str, user_id: int) -> None:
    requirement = get_requirement(db, raw_id)
    removed_name = requirement.name
    requirement.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, requirement.id, "Document requirement removed", user_id, previous_value=removed_name)
    db.commit()


def _resolve_target_catalog_id(db: Session, target_type: str, raw_id: str) -> int:
    """Resolves a target's display id ("ACT-004"/"PER-003") against
    whichever catalog target_type names -- Permit uses
    permit_catalog_items, Design/Supervision both use
    service_catalog_activities (the branch isn't re-checked here,
    unlike PermitPrerequisite/SupervisionPrerequisite, since a document
    requirement's usefulness doesn't depend on which branch its target
    activity is in)."""
    if target_type == "Permit":
        return permit_catalog_service.get_permit(db, raw_id).id
    return service_catalog_service.get_activity(db, raw_id).id


def list_links_for_catalog_id(db: Session, target_type: str, target_catalog_id: int) -> list[DocumentRequirementLink]:
    return (
        db.query(DocumentRequirementLink)
        .filter(DocumentRequirementLink.target_type == target_type, DocumentRequirementLink.target_catalog_id == target_catalog_id)
        .all()
    )


def list_links_for_target(db: Session, target_type: str, target_raw_id: str) -> list[DocumentRequirementLink]:
    catalog_id = _resolve_target_catalog_id(db, target_type, target_raw_id)
    return list_links_for_catalog_id(db, target_type, catalog_id)


def list_links_for_requirement(db: Session, requirement_raw_id: str) -> list[DocumentRequirementLink]:
    requirement = get_requirement(db, requirement_raw_id)
    return (
        db.query(DocumentRequirementLink)
        .filter(DocumentRequirementLink.document_requirement_id == requirement.id)
        .all()
    )


def add_link(db: Session, requirement_raw_id: str, target_type: str, target_raw_id: str) -> DocumentRequirementLink:
    requirement = get_requirement(db, requirement_raw_id)
    catalog_id = _resolve_target_catalog_id(db, target_type, target_raw_id)
    existing = (
        db.query(DocumentRequirementLink)
        .filter(
            DocumentRequirementLink.document_requirement_id == requirement.id,
            DocumentRequirementLink.target_type == target_type,
            DocumentRequirementLink.target_catalog_id == catalog_id,
        )
        .first()
    )
    if existing is not None:
        return existing
    link = DocumentRequirementLink(
        document_requirement_id=requirement.id, target_type=target_type, target_catalog_id=catalog_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_link(db: Session, link_id: int) -> None:
    link = db.query(DocumentRequirementLink).filter(DocumentRequirementLink.id == link_id).first()
    if link is None:
        raise NotFoundError("Document requirement link")
    db.delete(link)
    db.commit()


# --- per-project checklist fulfillment (#4/#5) -- the part that actually
# gates something, unlike everything above.

def list_fulfillments_for_project(db: Session, project_id: int) -> dict[int, ProjectDocumentRequirementFulfillment]:
    """Keyed by document_requirement_link_id, for O(1) lookup against a
    list of links (see api/projects.py's checklist endpoint, which
    zips this against list_links_for_catalog_id's result)."""
    rows = (
        db.query(ProjectDocumentRequirementFulfillment)
        .filter(ProjectDocumentRequirementFulfillment.project_id == project_id)
        .all()
    )
    return {row.document_requirement_link_id: row for row in rows}


def set_fulfillment(
    db: Session, project: Project, link_id: int, fulfilled: bool, document_id: int | None, user_id: int,
) -> ProjectDocumentRequirementFulfillment | None:
    """Checks or unchecks one checklist item for this project. Returns
    None when unchecking a item that was never checked in the first
    place (nothing to do) rather than creating an all-empty row --
    "checked, and by whom, and when" (see the model's own docstring)
    has nothing to say about an item nobody has touched yet."""
    link = db.query(DocumentRequirementLink).filter(DocumentRequirementLink.id == link_id).first()
    if link is None:
        raise NotFoundError("Document requirement link")
    row = (
        db.query(ProjectDocumentRequirementFulfillment)
        .filter(
            ProjectDocumentRequirementFulfillment.project_id == project.id,
            ProjectDocumentRequirementFulfillment.document_requirement_link_id == link_id,
        )
        .first()
    )
    if not fulfilled:
        if row is not None:
            db.delete(row)
            db.commit()
        return None
    if row is None:
        row = ProjectDocumentRequirementFulfillment(project_id=project.id, document_requirement_link_id=link_id)
        db.add(row)
    row.document_id = document_id
    row.fulfilled_at = datetime.now(timezone.utc)
    row.fulfilled_by = user_id
    db.commit()
    db.refresh(row)
    return row


def _resolve_selected_item_catalog_id(db: Session, target_type: str, selected_row) -> int | None:
    """selected_row is this project's own ProjectSelectedActivity/
    ProjectSelectedPermit/ProjectSelectedSupervisionActivity row --
    resolves it to the catalog row list_links_for_catalog_id needs.
    Permits carry a real FK (permit_catalog_item_id) already; Design/
    Supervision only kept the catalog's display id as an immutable
    snapshot (see ProjectSelectedActivity's own docstring for why), so
    those two need resolving the same way _resolve_target_catalog_id
    above does for the admin-facing (catalog-only, no project) side of
    this. Returns None -- fail-open -- if that catalog row has since
    been renamed/removed and can no longer be resolved at all; there's
    nothing left to check a real project's checklist against."""
    if target_type == "Permit":
        return selected_row.permit_catalog_item_id
    try:
        return service_catalog_service.get_activity(db, selected_row.activity_id).id
    except NotFoundError:
        return None


def list_links_for_selected_item(db: Session, target_type: str, selected_row) -> list[DocumentRequirementLink]:
    """Public entry point for api/projects.py's checklist endpoints --
    resolves selected_row (this project's own ProjectSelectedActivity/
    ProjectSelectedPermit/ProjectSelectedSupervisionActivity row) to its
    catalog links the same way list_outstanding_checklist_items below
    does internally, but returns the links themselves (for display,
    fulfilled or not) rather than just the outstanding names."""
    catalog_id = _resolve_selected_item_catalog_id(db, target_type, selected_row)
    if catalog_id is None:
        return []
    return list_links_for_catalog_id(db, target_type, catalog_id)


def list_outstanding_checklist_items(db: Session, project: Project, target_type: str, selected_row) -> list[str]:
    """Requirement names still unchecked for this project's copy of
    this Design activity/Permit/Supervision activity/permit -- empty if
    there's nothing linked to it, or if it can no longer be resolved
    against the catalog at all (see _resolve_selected_item_catalog_id).
    Used both by assert_checklist_fulfilled below (closing one item)
    and directly by project_service._assert_stage_exit_criteria's
    Handover branch (closing the whole project, one problem string per
    still-open item across every track, same as its sibling "every
    Design activity closed" checks)."""
    links = list_links_for_selected_item(db, target_type, selected_row)
    if not links:
        return []
    link_ids = [link.id for link in links]
    fulfilled_link_ids = {
        row[0] for row in db.query(ProjectDocumentRequirementFulfillment.document_requirement_link_id).filter(
            ProjectDocumentRequirementFulfillment.project_id == project.id,
            ProjectDocumentRequirementFulfillment.document_requirement_link_id.in_(link_ids),
            ProjectDocumentRequirementFulfillment.fulfilled_at.isnot(None),
        ).all()
    }
    outstanding_requirement_ids = {link.document_requirement_id for link in links if link.id not in fulfilled_link_ids}
    if not outstanding_requirement_ids:
        return []
    return [
        r.name for r in db.query(DocumentRequirement)
        .filter(DocumentRequirement.id.in_(outstanding_requirement_ids))
        .order_by(DocumentRequirement.name.asc())
        .all()
    ]


def assert_checklist_fulfilled(
    db: Session, project: Project, target_type: str, selected_row, override_no_document: bool = False,
) -> None:
    """The actual gate (#4) -- called by close_design_activity/
    set_permit_status/set_supervision_status right alongside
    project_service._assert_completion_evidence, and meant to sit next
    to it rather than replace it: override_no_document, when given,
    forgives this one exactly the same way that one's own override
    does. Nothing calls this with an override at the Handover exit
    criterion (project_service._assert_stage_exit_criteria) -- by the
    time a whole project is being handed over, "check the box or
    reopen/cancel the item" is the only way through, the same
    no-override stance project_service._assert_design_tasks_complete
    already takes on task completion."""
    if override_no_document:
        return
    outstanding = list_outstanding_checklist_items(db, project, target_type, selected_row)
    if outstanding:
        raise ValidationAppError(
            "Complete the handover document checklist first -- still outstanding: " + ", ".join(outstanding)
        )
