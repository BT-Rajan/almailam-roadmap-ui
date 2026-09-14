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
    SubmissionUpdate,
    check_response_outcome,
)
from app.services import submission_service

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

can_view = require_permission("Government", "view")
# Deliberately not gated on the "Government: edit" role permission --
# any authenticated user can create/edit/manage a permit application,
# not just roles that have been granted that permission in
# Administration > Roles & Permissions. Still requires being logged in.
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


def _to_out_batch(db: Session, submissions: list) -> list[SubmissionOut]:
    """Batched sibling of _to_out -- for a list of submissions, resolves
    every project and every document-uploader/proof-uploader name with a
    constant number of queries total (one for projects, one for all
    documents, one for all users) instead of _to_out's several queries
    per submission. Same output shape as calling _to_out on each."""
    if not submissions:
        return []

    project_ids = {s.project_id for s in submissions}
    project_nos = {
        p.id: p.project_no for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
    }

    documents_by_submission = submission_service.get_documents_by_submission(db, [s.id for s in submissions])

    user_ids: set[int] = set()
    for submission in submissions:
        user_ids.add(submission.proof_of_submission_uploaded_by)
        user_ids.add(submission.proof_of_response_uploaded_by)
    for documents in documents_by_submission.values():
        user_ids.update(d.uploaded_by for d in documents)
    names = submission_service.user_names(db, user_ids)

    def _name(user_id: int | None) -> str | None:
        if user_id is None:
            return None
        return names.get(user_id, "Unknown")

    out = []
    for submission in submissions:
        documents = documents_by_submission.get(submission.id, [])
        out.append(
            SubmissionOut.from_model(
                submission,
                project_nos.get(submission.project_id, ""),
                documents,
                document_uploader_names={
                    d.id: names.get(d.uploaded_by, "Unknown") for d in documents if d.uploaded_by
                },
                proof_of_submission_uploader_name=_name(submission.proof_of_submission_uploaded_by),
                proof_of_response_uploader_name=_name(submission.proof_of_response_uploaded_by),
            )
        )
    return out


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    projectId: str | None = None,
    stage: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    submissions = submission_service.list_submissions(db, projectId, stage)
    return _to_out_batch(db, submissions)


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


@router.post("/{submission_no}/confirm-readiness", response_model=SubmissionOut)
def confirm_readiness(submission_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    """Prepare -> Apply: every required document is Uploaded/Verified
    and staff explicitly confirm the application is ready to file."""
    submission_service.confirm_readiness(db, submission_no, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.post("/{submission_no}/acknowledgement", response_model=SubmissionOut, status_code=201)
def record_acknowledgement(
    submission_no: str,
    acknowledgementNumber: str | None = Form(None),
    paymentReference: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    """Apply -> Track: files the application -- the authority's
    acknowledgement number/date, an optional payment reference, and the
    acknowledgement document itself."""
    submission_service.record_acknowledgement(
        db, submission_no, file, acknowledgementNumber, paymentReference, notes, current_user.id
    )
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/acknowledgement/download")
def download_acknowledgement(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = submission_service.get_proof_of_submission_download_target(db, submission_no)
    return FileResponse(path, filename=original_filename)


@router.post("/{submission_no}/close", response_model=SubmissionOut)
def close_application(
    submission_no: str,
    outcome: str = Form(...),
    closingNotes: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    """-> Close: the final outcome (Approved/Rejected/No Response/
    Withdrawn), an optional permit/decision document, and closing
    notes. Reachable from any stage."""
    checked_outcome = check_response_outcome(outcome)
    submission_service.close_application(db, submission_no, checked_outcome, closingNotes, file, current_user.id)
    return _to_out(db, submission_service.get_submission(db, submission_no))


@router.get("/{submission_no}/permit-document/download")
def download_permit_document(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = submission_service.get_proof_of_response_download_target(db, submission_no)
    return FileResponse(path, filename=original_filename)


@router.get("/{submission_no}/followups", response_model=list[FollowupOut])
def list_followups(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    submission = submission_service.get_submission(db, submission_no)
    followups = submission_service.get_followups(db, submission.id)
    return [FollowupOut.from_model(f, submission_service.user_name(db, f.created_by)) for f in followups]


@router.post("/{submission_no}/followups", response_model=FollowupOut, status_code=201)
def add_followup(
    submission_no: str,
    entryStage: str = Form(...),
    followupDate: str = Form(...),
    followupTime: str = Form(...),
    contactPerson: str = Form(...),
    notes: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    """Logs contact with the authority. entryStage 'Track' for a plain
    check-in, 'Update' (with an optional document) for one where the
    authority asked for something else -- either moves/keeps the
    application at that stage."""
    payload = FollowupCreate(
        entryStage=entryStage, followupDate=followupDate, followupTime=followupTime,
        contactPerson=contactPerson, notes=notes,
    )
    followup = submission_service.add_followup(
        db, submission_no, payload.entryStage, payload.followupDate, payload.followupTime,
        payload.contactPerson, payload.notes, file, current_user.id,
    )
    return FollowupOut.from_model(followup, current_user.full_name)


@router.get("/{submission_no}/followups/{followup_id}/download")
def download_followup_document(
    submission_no: str, followup_id: str, db: Session = Depends(get_db), _=Depends(can_view)
):
    path, original_filename = submission_service.get_followup_document_download_target(
        db, submission_no, submission_service.parse_followup_id(followup_id)
    )
    return FileResponse(path, filename=original_filename)


@router.get("/{submission_no}/audit-events")
def list_audit_events(submission_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return submission_service.get_audit_events(db, submission_no)
