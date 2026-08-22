from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.government import (
    SubmissionCreate,
    SubmissionDocumentStatusUpdate,
    SubmissionOut,
    SubmissionStatusUpdate,
    SubmissionUpdate,
)
from app.services import submission_service

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

can_view = require_permission("Government", "view")
# Deliberately not gated on the "Government: edit" role permission --
# any authenticated user can create/edit/manage a submission, not just
# roles that have been granted that permission in Administration >
# Roles & Permissions. Still requires being logged in.
can_edit = get_current_user


def _to_out(db: Session, submission) -> SubmissionOut:
    project = db.query(Project).filter(Project.id == submission.project_id).first()
    documents = submission_service.get_documents(db, submission.id)
    return SubmissionOut.from_model(submission, project.project_no if project else "", documents)


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    projectId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    submissions = submission_service.list_submissions(db, projectId, status)
    return [_to_out(db, s) for s in submissions]


@router.get("/{submission_no}", response_model=SubmissionOut)
def get_submission(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    submission = submission_service.get_submission(db, submission_no)
    return _to_out(db, submission)


@router.post("", response_model=SubmissionOut, status_code=201)
def create_submission(
    payload: SubmissionCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    submission = submission_service.create_submission(db, payload, current_user.id)
    return _to_out(db, submission)


@router.patch("/{submission_no}", response_model=SubmissionOut)
def update_submission(
    submission_no: str,
    payload: SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    submission = submission_service.update_submission(db, submission_no, payload, current_user.id)
    return _to_out(db, submission)


@router.patch("/{submission_no}/status", response_model=SubmissionOut)
def set_status(
    submission_no: str,
    payload: SubmissionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    submission = submission_service.set_status(
        db, submission_no, payload.status, payload.reason, current_user.id
    )
    return _to_out(db, submission)


@router.patch("/{submission_no}/documents/{document_id}")
def set_document_status(
    submission_no: str,
    document_id: int,
    payload: SubmissionDocumentStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(can_edit),
):
    document = submission_service.set_document_status(db, submission_no, document_id, payload.status)
    return {"name": document.name, "status": document.status}


@router.get("/{submission_no}/audit-events")
def list_audit_events(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return submission_service.get_audit_events(db, submission_no)
