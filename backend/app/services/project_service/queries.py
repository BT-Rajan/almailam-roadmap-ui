"""Read-only project lookups: list/get a project or its selected
Design/Permit/Supervision activities, plus its audit trail.

First extraction out of the old monolithic project_service.py (see the
package's __init__.py for the rest, still pending its own split). This
group was picked to go first specifically because none of these
functions mutate any state -- they only ever run a query and return
it -- which makes them the lowest-risk piece to move: there's no
ordering, no side effect, and no interaction with the rest of the
module's business logic to get subtly wrong in transit. Every function
here was moved verbatim; nothing about their behavior changed as part
of this split.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.models.permit_selection import ProjectSelectedPermit
from app.models.project import Project, ProjectSelectedActivity, ProjectSelectedSupervisionActivity
from app.models.user import User
from app.services import audit_service, client_service, user_service
from app.services.project_service._shared import ENTITY_TYPE

# Columns the project list can be sorted on via ?sort=field / ?sort=-field.
# Deliberately limited to real columns on the table -- "clientName" and
# "engineer" are resolved from other tables per-row and are not sortable
# without a join, so they're intentionally left out here.
PROJECT_SORTABLE_FIELDS = {
    "projectNo": Project.project_no,
    "projectName": Project.project_name,
    "status": Project.status,
    "currentStage": Project.current_stage,
    "progress": Project.progress,
    "targetDate": Project.target_date,
}


def engineer_name(db: Session, engineer_id: int) -> str:
    user = db.query(User).filter(User.id == engineer_id).first()
    return user.full_name if user else "Unknown"


def engineer_names(db: Session, engineer_ids: set[int]) -> dict[int, str]:
    """Batch lookup used by the list endpoint so it doesn't run one query
    per row (see engineer_name for the single-id version used elsewhere)."""
    if not engineer_ids:
        return {}
    return dict(db.query(User.id, User.full_name).filter(User.id.in_(engineer_ids)).all())


def list_projects(
    db: Session,
    client_id: str | None = None,
    status: str | None = None,
    stage: str | None = None,
    engineer_id: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    deleted: bool = False,
) -> dict:
    query = db.query(Project).filter(Project.deleted_at.isnot(None) if deleted else Project.deleted_at.is_(None))
    if client_id:
        query = query.filter(Project.client_id == client_service.parse_client_id(client_id))
    if status:
        query = query.filter(Project.status == status)
    if stage:
        query = query.filter(Project.current_stage == stage)
    if engineer_id:
        query = query.filter(Project.engineer_id == user_service.parse_user_id(engineer_id))
    if search:
        term = f"%{search.strip()}%"
        conditions = [
            Project.project_no.ilike(term),
            Project.project_name.ilike(term),
            Project.service.ilike(term),
        ]
        matching_engineer_ids = [
            row[0] for row in db.query(User.id).filter(User.full_name.ilike(term)).all()
        ]
        if matching_engineer_ids:
            conditions.append(Project.engineer_id.in_(matching_engineer_ids))
        query = query.filter(or_(*conditions))
    return sort_and_paginate(query, Project, PROJECT_SORTABLE_FIELDS, sort, page, page_size)


def get_project(db: Session, project_no: str) -> Project:
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.is_(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Project")
    return project


def get_selected_activities(db: Session, project_id: int) -> list[ProjectSelectedActivity]:
    return (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.project_id == project_id)
        .order_by(ProjectSelectedActivity.id.asc())
        .all()
    )


def get_selected_activities_batch(db: Session, project_ids: set[int]) -> dict[int, list[ProjectSelectedActivity]]:
    """Batch version of get_selected_activities for list endpoints, so
    rendering a page of projects doesn't run one query per row (same
    pattern as engineer_names above)."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedActivity]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.project_id.in_(project_ids))
        .order_by(ProjectSelectedActivity.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def get_selected_supervision_activities(db: Session, project_id: int) -> list[ProjectSelectedSupervisionActivity]:
    return (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(ProjectSelectedSupervisionActivity.project_id == project_id)
        .order_by(ProjectSelectedSupervisionActivity.id.asc())
        .all()
    )


def get_selected_supervision_activities_batch(
    db: Session, project_ids: set[int]
) -> dict[int, list[ProjectSelectedSupervisionActivity]]:
    """Batch version of get_selected_supervision_activities, same
    reasoning as get_selected_activities_batch above."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedSupervisionActivity]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(ProjectSelectedSupervisionActivity.project_id.in_(project_ids))
        .order_by(ProjectSelectedSupervisionActivity.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def get_selected_permits(db: Session, project_id: int) -> list[ProjectSelectedPermit]:
    return (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.project_id == project_id)
        .order_by(ProjectSelectedPermit.id.asc())
        .all()
    )


def get_selected_permits_batch(db: Session, project_ids: set[int]) -> dict[int, list[ProjectSelectedPermit]]:
    """Batch version of get_selected_permits, same reasoning as
    get_selected_activities_batch above."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedPermit]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.project_id.in_(project_ids))
        .order_by(ProjectSelectedPermit.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def get_selected_activity(db: Session, project_id: int, activity_id: int) -> ProjectSelectedActivity:
    """A single Design activity row, scoped to a specific project so a
    caller can't operate on another project's row just by knowing its
    raw id."""
    activity = (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.id == activity_id, ProjectSelectedActivity.project_id == project_id)
        .first()
    )
    if activity is None:
        raise NotFoundError("Selected activity")
    return activity


def get_selected_permit(db: Session, project_id: int, permit_id: int) -> ProjectSelectedPermit:
    """A single Permit row, scoped to a specific project so a caller
    can't operate on another project's row just by knowing its raw
    id -- same reasoning as get_selected_activity above."""
    permit = (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.id == permit_id, ProjectSelectedPermit.project_id == project_id)
        .first()
    )
    if permit is None:
        raise NotFoundError("Selected permit")
    return permit


def get_selected_supervision_activity(
    db: Session, project_id: int, activity_id: int
) -> ProjectSelectedSupervisionActivity:
    """A single Supervision activity row, scoped to a specific project --
    same reasoning as get_selected_activity/get_selected_permit above."""
    activity = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(
            ProjectSelectedSupervisionActivity.id == activity_id,
            ProjectSelectedSupervisionActivity.project_id == project_id,
        )
        .first()
    )
    if activity is None:
        raise NotFoundError("Selected supervision activity")
    return activity


def _project_exists(db: Session, project_no: str) -> Project:
    """Like get_project() but doesn't exclude soft-deleted projects --
    used only for read-only historical views (audit trail) where a
    deleted project's own history must remain inspectable. Everything
    else (updates, timeline entries, etc.) keeps using get_project() so
    a soft-deleted project stays fully locked for writes."""
    project = db.query(Project).filter(Project.project_no == project_no).first()
    if project is None:
        raise NotFoundError("Project")
    return project


def get_audit_events(db: Session, project_no: str) -> list[dict]:
    project = _project_exists(db, project_no)
    return audit_service.get_history(db, ENTITY_TYPE, project.id)
