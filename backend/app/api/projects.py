from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.project import (
    CompletionNotesUpdate,
    CompletionChecklistOut,
    CompletionSummaryOut,
    DeviationNotesUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectStageUpdate,
    ProjectStatusUpdate,
    ProjectUpdate,
    ScopeChangeUpdate,
    ScopeCompletionSummaryOut,
    ScopeItemCompletionUpdate,
    AdditionalExecutionStepUpdate,
    ScopeOfWorkOut,
    ScopeRevisionOut,
)
from app.schemas.timeline import TimelineEventCreate, TimelineEventOut, TimelineEventUpdate
from app.services import project_service, timeline_service

router = APIRouter(prefix="/api/projects", tags=["projects"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _project_out(db: Session, project, engineer_name: str) -> ProjectOut:
    activities = project_service.get_selected_activities(db, project.id)
    type_activities = project_service.get_selected_type_activities(db, project.id)
    return ProjectOut.from_model(project, engineer_name, activities, type_activities)


def _scope_of_work_out(db: Session, project) -> ScopeOfWorkOut:
    revisions = project_service.get_scope_revisions_with_names(db, project.id)
    approved_by_name = (
        project_service.engineer_name(db, project.scope_approved_by) if project.scope_approved_by else None
    )
    return ScopeOfWorkOut(
        description=project.description,
        scopeStatus=project.scope_status,
        scopeApprovedAt=project.scope_approved_at,
        scopeApprovedBy=approved_by_name,
        revisions=[ScopeRevisionOut.from_model(revision, name) for revision, name in revisions],
    )


@router.get("", response_model=PagedResponse[ProjectOut])
def list_projects(
    clientId: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    stage: str | None = None,
    engineerId: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    result = project_service.list_projects(db, clientId, status, priority, stage, engineerId, search, sort, page, pageSize)
    engineer_ids = {p.engineer_id for p in result["items"]}
    names = project_service.engineer_names(db, engineer_ids)
    activities_by_project = project_service.get_selected_activities_batch(db, {p.id for p in result["items"]})
    type_activities_by_project = project_service.get_selected_type_activities_batch(db, {p.id for p in result["items"]})
    result["items"] = [
        ProjectOut.from_model(
            p, names.get(p.engineer_id, "Unknown"),
            activities_by_project.get(p.id, []),
            type_activities_by_project.get(p.id, []),
        )
        for p in result["items"]
    ]
    return result


@router.get("/{project_no}", response_model=ProjectOut)
def get_project(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.create_project(db, payload, current_user.id)
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}", response_model=ProjectOut)
def update_project(
    project_no: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.update_project(db, project_no, payload, current_user.id)
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}/stage", response_model=ProjectOut)
def set_stage(
    project_no: str,
    payload: ProjectStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.set_stage(
        db, project_no, payload.currentStage, payload.reason, current_user.id
    )
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}/status", response_model=ProjectOut)
def set_status(
    project_no: str,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.set_status(
        db, project_no, payload.status, payload.reason, current_user.id
    )
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.get("/{project_no}/completion-summary", response_model=CompletionSummaryOut)
def get_completion_summary(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return project_service.get_completion_summary(db, project_no)


@router.get("/{project_no}/completion-checklist", response_model=CompletionChecklistOut)
def get_completion_checklist(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return project_service.get_completion_checklist(db, project_no)


@router.patch("/{project_no}/completion-notes", response_model=CompletionSummaryOut)
def update_completion_notes(
    project_no: str,
    payload: CompletionNotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project_service.update_completion_notes(db, project_no, payload.notes, current_user.id)
    return project_service.get_completion_summary(db, project_no)


@router.patch("/{project_no}/deviation-notes", response_model=CompletionSummaryOut)
def update_deviation_notes(
    project_no: str,
    payload: DeviationNotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project_service.update_deviation_notes(db, project_no, payload.notes, current_user.id)
    return project_service.get_completion_summary(db, project_no)


@router.patch("/{project_no}/scope", response_model=ProjectOut)
def change_scope(
    project_no: str,
    payload: ScopeChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.change_scope(
        db, project_no, payload.description, payload.contractUpdateNeeded, payload.paymentUpdateNeeded, current_user.id
    )
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.get("/{project_no}/scope-of-work", response_model=ScopeOfWorkOut)
def get_scope_of_work(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    return _scope_of_work_out(db, project)


@router.post("/{project_no}/scope-of-work", response_model=ScopeOfWorkOut)
def save_scope_of_work(
    project_no: str,
    scopeText: str = Form(...),
    summary: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.save_scope_of_work(db, project_no, scopeText, summary, current_user.id, file)
    return _scope_of_work_out(db, project)


@router.post("/{project_no}/scope-of-work/approve", response_model=ProjectOut)
def approve_scope_of_work(project_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    project = project_service.approve_scope_of_work(db, project_no, current_user.id)
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.get("/{project_no}/scope-of-work/{revision_id}/document")
def download_scope_revision_document(
    project_no: str, revision_id: str, db: Session = Depends(get_db), _=Depends(can_view)
):
    project = project_service.get_project(db, project_no)
    numeric_id = revision_id.removeprefix("PSR-") if revision_id.upper().startswith("PSR-") else revision_id
    path, original_filename = project_service.get_scope_revision_download_target(db, project.id, int(numeric_id))
    return FileResponse(path, filename=original_filename)


@router.get("/{project_no}/audit-events")
def list_audit_events(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return project_service.get_audit_events(db, project_no)


@router.get("/{project_no}/scope-completion", response_model=ScopeCompletionSummaryOut)
def get_scope_completion(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    return project_service.get_scope_completion_summary(db, project.id)


@router.patch("/{project_no}/scope-items", response_model=ProjectOut)
def update_scope_item_completion(
    project_no: str,
    payload: ScopeItemCompletionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.set_scope_item_complete(
        db, project_no, payload.source, payload.itemId, payload.isComplete, current_user.id,
    )
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}/execution-steps/{step_id}/additional", response_model=ProjectOut)
def mark_additional_execution_step(
    project_no: str,
    step_id: str,
    payload: AdditionalExecutionStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.mark_additional_execution_step(db, project_no, step_id, payload.contractCovered, current_user.id)
    return _project_out(db, project, project_service.engineer_name(db, project.engineer_id))


@router.get("/{project_no}/timeline", response_model=list[TimelineEventOut])
def list_timeline(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    events = timeline_service.list_for_project(db, project_no)
    return [
        TimelineEventOut.from_model(e, project_no, timeline_service.user_name(db, e.created_by))
        for e in events
    ]


@router.post("/{project_no}/timeline", response_model=TimelineEventOut, status_code=201)
def create_timeline_event(
    project_no: str,
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    event = timeline_service.create_event(db, project_no, payload, current_user.id)
    return TimelineEventOut.from_model(event, project_no, current_user.full_name)


@router.patch("/{project_no}/timeline/{event_id}", response_model=TimelineEventOut)
def update_timeline_event(
    project_no: str,
    event_id: str,
    payload: TimelineEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    event = timeline_service.update_event(db, project_no, event_id, payload)
    return TimelineEventOut.from_model(event, project_no, timeline_service.user_name(db, event.created_by))


@router.delete("/{project_no}", status_code=204)
def delete_project(project_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    project_service.delete_project(db, project_no, current_user.id)
