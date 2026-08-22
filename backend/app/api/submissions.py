from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.government import (
    FollowupCreate,
    FollowupOut,
    SubmissionCreate,
    SubmissionDocumentStatusUpdate,
    SubmissionOut,
    SubmissionStatusUpdate,
    SubmissionUpdate,
    check_response_outcome,
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
    uploader_names = {d.id: submission_service.user_name(db, d.uploaded_by) for d in documents if d.uploaded_by}
    return SubmissionOut.from_model(
        submission,
        project.project_no if project else "",
        documents,
        document_uploader_names=uploader_names,
        proof_of_submission_uploader_name=submission_service.user_name(db, submission.proof_of_submission_uploaded_by)
        if submission.proof_of_submission_uploaded_by
        else None,
        proof_of_response_uploader_name=submission_service.user_name(db, submission.proof_of_response_uploaded_by)
        if submission.proof_of_response_uploaded_by
        else None,
    )


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


@router.post("/{submission_no}/documents/{document_id}/upload", response_model=SubmissionOut)
def upload_document(
    submission_no: str,
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    submission_service.upload_document(db, submission_no, document_id, file, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/documents/{document_id}/download")
def download_document(
    submission_no: str, document_id: int, db: Session = Depends(get_db), _=Depends(can_view)
):
    path, original_filename = submission_service.get_document_download_target(db, submission_no, document_id)
    return FileResponse(path, filename=original_filename)


@router.post("/{submission_no}/proof-of-submission", response_model=SubmissionOut, status_code=201)
def upload_proof_of_submission(
    submission_no: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    submission_service.upload_proof_of_submission(db, submission_no, file, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/proof-of-submission/download")
def download_proof_of_submission(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = submission_service.get_proof_of_submission_download_target(db, submission_no)
    return FileResponse(path, filename=original_filename)


@router.post("/{submission_no}/proof-of-response", response_model=SubmissionOut, status_code=201)
def upload_proof_of_response(
    submission_no: str,
    outcome: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    checked_outcome = check_response_outcome(outcome)
    submission_service.upload_proof_of_response(db, submission_no, file, checked_outcome, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/proof-of-response/download")
def download_proof_of_response(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = submission_service.get_proof_of_response_download_target(db, submission_no)
    return FileResponse(path, filename=original_filename)


@router.post("/{submission_no}/complete", response_model=SubmissionOut)
def mark_complete(submission_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    submission_service.mark_complete(db, submission_no, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/followups", response_model=list[FollowupOut])
def list_followups(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    submission = submission_service.get_submission(db, submission_no)
    followups = submission_service.get_followups(db, submission.id)
    return [FollowupOut.from_model(f, submission_service.user_name(db, f.created_by)) for f in followups]


@router.post("/{submission_no}/followups", response_model=FollowupOut, status_code=201)
def add_followup(
    submission_no: str,
    payload: FollowupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    followup = submission_service.add_followup(
        db, submission_no, payload.followupDate, payload.followupTime, payload.contactPerson,
        payload.notes, current_user.id,
    )
    return FollowupOut.from_model(followup, current_user.full_name)


@router.get("/{submission_no}/audit-events")
def list_audit_events(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return submission_service.get_audit_events(db, submission_no)
