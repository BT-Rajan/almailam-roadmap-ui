from datetime import date

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.status_transitions import (
    SUBMISSION_ALLOWED_TRANSITIONS,
    SUBMISSION_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.government import GovernmentSubmission, SubmissionDocument, SubmissionFollowup
from app.models.project import Project
from app.models.user import User
from app.services import audit_service, government_service, project_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "GOVERNMENT_SUBMISSION"
UPLOAD_SUBDIRECTORY = "submissions"

# Statuses in which a follow-up call/visit or a proof-of-response upload
# makes sense -- i.e. the submission has actually gone out and is awaiting
# a decision from the authority.
AWAITING_RESPONSE_STATUSES = ("Submitted", "Under Review", "Comments Received")


def user_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "System"
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _parse_project_id_from_no(project_no: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def list_submissions(
    db: Session, project_no: str | None = None, status: str | None = None
) -> list[GovernmentSubmission]:
    query = db.query(GovernmentSubmission).filter(GovernmentSubmission.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(GovernmentSubmission.project_id == (project.id if project else -1))
    if status:
        query = query.filter(GovernmentSubmission.status == status)
    return query.order_by(GovernmentSubmission.id.asc()).all()


def get_submission(db: Session, submission_no: str) -> GovernmentSubmission:
    submission = (
        db.query(GovernmentSubmission)
        .filter(GovernmentSubmission.submission_no == submission_no, GovernmentSubmission.deleted_at.is_(None))
        .first()
    )
    if submission is None:
        raise NotFoundError("Submission")
    return submission


def get_documents(db: Session, submission_id: int) -> list[SubmissionDocument]:
    return (
        db.query(SubmissionDocument)
        .filter(SubmissionDocument.submission_id == submission_id)
        .order_by(SubmissionDocument.id.asc())
        .all()
    )


def create_submission(db: Session, payload, user_id: int | None) -> GovernmentSubmission:
    project = _parse_project_id_from_no(payload.projectId, db)
    authority_id = government_service.parse_authority_id(payload.authorityId)
    form_id = government_service.parse_form_id(payload.formId)
    government_service.get_authority(db, authority_id)  # 404 if unknown
    form = government_service.get_form(db, form_id)

    submission_no = next_number(db, "GOVERNMENT_SUBMISSION")
    submission = GovernmentSubmission(
        submission_no=submission_no,
        project_id=project.id,
        authority_id=authority_id,
        form_id=form_id,
        expected_decision_date=payload.expectedDecisionDate,
        notes=payload.notes,
    )
    db.add(submission)
    db.flush()

    # Seed the per-submission document checklist from the form's required
    # documents template -- each starts Pending until uploaded/verified.
    for document_name in form.required_documents:
        db.add(SubmissionDocument(submission_id=submission.id, name=document_name, status="Pending"))

    audit_service.log_event(db, ENTITY_TYPE, submission.id, "Submission created", user_id, new_value=submission.submission_no)
    timeline_service.create_system_event(
        db, project.id, "submission",
        title=f"Government submission {submission.submission_no} created",
        actor_id=user_id,
    )
    db.commit()
    db.refresh(submission)
    return submission


def update_submission(db: Session, submission_no: str, payload, user_id: int | None) -> GovernmentSubmission:
    submission = get_submission(db, submission_no)
    changes: dict[str, tuple] = {}
    if payload.expectedDecisionDate is not None and payload.expectedDecisionDate != submission.expected_decision_date:
        changes["expected_decision_date"] = (submission.expected_decision_date, payload.expectedDecisionDate)
        submission.expected_decision_date = payload.expectedDecisionDate
    if payload.notes is not None and payload.notes != submission.notes:
        changes["notes"] = (submission.notes, payload.notes)
        submission.notes = payload.notes

    audit_service.log_field_changes(db, ENTITY_TYPE, submission.id, changes, user_id)
    db.commit()
    db.refresh(submission)

    if payload.status is not None and payload.status != submission.status:
        submission = set_status(db, submission_no, payload.status, payload.reason, user_id)

    return submission


def set_status(
    db: Session, submission_no: str, new_status: str, reason: str | None, user_id: int | None
) -> GovernmentSubmission:
    submission = get_submission(db, submission_no)
    assert_transition_allowed(SUBMISSION_ALLOWED_TRANSITIONS, submission.status, new_status, "submission")
    if new_status in SUBMISSION_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the submission to '{new_status}'.")

    # An authority approving a submission implies every document it asked
    # for has actually been provided, not left at "Pending" (never even
    # uploaded) -- that's a real state a reviewer could otherwise put the
    # record in by clicking through the status dropdown directly instead
    # of going through mark_complete(). Reuses the same bar
    # all_documents_satisfied() already uses elsewhere in this file
    # ("Uploaded" or "Verified") rather than inventing a stricter one --
    # this workflow has no separate verification step, so requiring
    # "Verified" specifically would make a fully-Approved,
    # fully-documented submission unable to ever complete. Only
    # "Approved" is gated, not "Submitted": paperwork can trail a
    # submission being filed, but the authority's own sign-off should mean
    # the checklist is actually done.
    if new_status == "Approved":
        documents = get_documents(db, submission.id)
        if not all_documents_satisfied(documents):
            missing = [d.name for d in documents if d.status not in ("Uploaded", "Verified")]
            raise ValidationAppError(
                f"Cannot approve this submission -- these required documents are still pending: {', '.join(missing)}."
            )

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Status changed", user_id,
        previous_value=submission.status, new_value=new_status, reason=reason,
    )
    submission.status = new_status
    # Realistic side effects matching how the dates actually get populated:
    # the submission date is set the first time it's actually submitted,
    # and the decision date when the authority hands down a decision.
    if new_status == "Submitted" and submission.submitted_date is None:
        submission.submitted_date = date.today()
    if new_status in ("Approved", "Rejected") and submission.decision_date is None:
        submission.decision_date = date.today()

    # An Approved submission is exactly what project_service's Government
    # Submission -> Supervision exit criterion requires -- flush first so
    # that check's own fresh query sees this row's new status (session is
    # autoflush=False), then let the same auto-advance path every other
    # stage-completing action goes through pick it up, instead of leaving
    # Supervision waiting on a separate manual "move stage" click.
    if new_status == "Approved":
        db.flush()
        project = db.query(Project).filter(Project.id == submission.project_id).first()
        if project is not None:
            project_service.try_auto_advance_stage(db, project, user_id)

    db.commit()
    db.refresh(submission)
    return submission


def set_document_status(
    db: Session, submission_no: str, document_id: int, new_status: str
) -> SubmissionDocument:
    submission = get_submission(db, submission_no)
    document = (
        db.query(SubmissionDocument)
        .filter(SubmissionDocument.id == document_id, SubmissionDocument.submission_id == submission.id)
        .first()
    )
    if document is None:
        raise NotFoundError("Submission document")
    document.status = new_status
    db.commit()
    db.refresh(document)
    return document


def _get_document(db: Session, submission: GovernmentSubmission, document_id: int) -> SubmissionDocument:
    document = (
        db.query(SubmissionDocument)
        .filter(SubmissionDocument.id == document_id, SubmissionDocument.submission_id == submission.id)
        .first()
    )
    if document is None:
        raise NotFoundError("Submission document")
    return document


def all_documents_satisfied(documents: list[SubmissionDocument]) -> bool:
    return bool(documents) and all(d.status in ("Uploaded", "Verified") for d in documents)


def upload_document(
    db: Session, submission_no: str, document_id: int, file: UploadFile, user_id: int | None
) -> SubmissionDocument:
    """Attach/replace the file behind one Required Documents checklist
    entry -- only while the submission is in Draft, matching the "move it
    to draft, then update each document as it becomes available" flow."""
    submission = get_submission(db, submission_no)
    if submission.status != "Draft":
        raise ValidationAppError("Required documents can only be updated while the submission is in Draft.")
    document = _get_document(db, submission, document_id)

    storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)
    document.storage_key = storage_key
    document.original_filename = original_filename
    document.file_size_bytes = size_bytes
    document.uploaded_by = user_id
    document.upload_date = date.today()
    if document.status == "Pending":
        document.status = "Uploaded"

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Required document uploaded", user_id, new_value=document.name
    )
    db.commit()
    db.refresh(document)
    return document


def get_document_download_target(db: Session, submission_no: str, document_id: int):
    submission = get_submission(db, submission_no)
    document = _get_document(db, submission, document_id)
    if document.storage_key is None:
        raise NotFoundError("Submission document file")
    return resolve_path(document.storage_key), document.original_filename


def upload_proof_of_submission(
    db: Session, submission_no: str, file: UploadFile, user_id: int | None
) -> GovernmentSubmission:
    """Records proof the form was actually handed to the authority, and
    moves the submission Draft -> Submitted. Gated on every required
    document being Uploaded/Verified first."""
    submission = get_submission(db, submission_no)
    if submission.status != "Draft":
        raise ValidationAppError("Proof of submission can only be uploaded while the submission is in Draft.")
    documents = get_documents(db, submission.id)
    if not all_documents_satisfied(documents):
        raise ValidationAppError("All required documents must be uploaded before recording proof of submission.")

    storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)
    submission.proof_of_submission_storage_key = storage_key
    submission.proof_of_submission_filename = original_filename
    submission.proof_of_submission_size_bytes = size_bytes
    submission.proof_of_submission_uploaded_by = user_id
    submission.proof_of_submission_upload_date = date.today()

    audit_service.log_event(db, ENTITY_TYPE, submission.id, "Proof of submission uploaded", user_id)
    db.commit()
    db.refresh(submission)

    return set_status(db, submission_no, "Submitted", None, user_id)


def get_proof_of_submission_download_target(db: Session, submission_no: str):
    submission = get_submission(db, submission_no)
    if submission.proof_of_submission_storage_key is None:
        raise NotFoundError("Proof of submission")
    return resolve_path(submission.proof_of_submission_storage_key), submission.proof_of_submission_filename


def upload_proof_of_response(
    db: Session, submission_no: str, file: UploadFile, outcome: str, user_id: int | None
) -> GovernmentSubmission:
    """Records the authority's decision letter/receipt and the outcome it
    conveys. Doesn't change status by itself -- see mark_complete for the
    step that actually closes the submission out on an Approved outcome."""
    submission = get_submission(db, submission_no)
    if submission.status not in AWAITING_RESPONSE_STATUSES:
        raise ValidationAppError(
            "Proof of response can only be uploaded once the submission has been sent to the authority."
        )

    storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)
    submission.proof_of_response_storage_key = storage_key
    submission.proof_of_response_filename = original_filename
    submission.proof_of_response_size_bytes = size_bytes
    submission.proof_of_response_uploaded_by = user_id
    submission.proof_of_response_upload_date = date.today()
    submission.response_outcome = outcome

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Proof of government response uploaded", user_id, new_value=outcome
    )
    db.commit()
    db.refresh(submission)
    return submission


def get_proof_of_response_download_target(db: Session, submission_no: str):
    submission = get_submission(db, submission_no)
    if submission.proof_of_response_storage_key is None:
        raise NotFoundError("Proof of response")
    return resolve_path(submission.proof_of_response_storage_key), submission.proof_of_response_filename


def mark_complete(db: Session, submission_no: str, user_id: int | None) -> GovernmentSubmission:
    """Closes the submission out as Approved once an Approved outcome has
    been recorded against an uploaded proof of response. Walks the status
    machine through 'Under Review' first when needed, since that's the
    only status the workflow allows a direct move to 'Approved' from."""
    submission = get_submission(db, submission_no)
    if submission.proof_of_response_storage_key is None:
        raise ValidationAppError("Upload proof of the government's response before marking this complete.")
    if submission.response_outcome != "Approved":
        raise ValidationAppError("This submission can only be marked complete once an Approved response is on file.")

    if submission.status in ("Submitted", "Comments Received"):
        set_status(db, submission_no, "Under Review", None, user_id)
    elif submission.status not in ("Under Review", "Approved"):
        raise ValidationAppError(f"Cannot mark complete from status '{submission.status}'.")

    submission = get_submission(db, submission_no)
    if submission.status == "Approved":
        return submission
    return set_status(db, submission_no, "Approved", None, user_id)


def get_followups(db: Session, submission_id: int) -> list[SubmissionFollowup]:
    return (
        db.query(SubmissionFollowup)
        .filter(SubmissionFollowup.submission_id == submission_id)
        .order_by(SubmissionFollowup.created_at.desc(), SubmissionFollowup.id.desc())
        .all()
    )


def add_followup(
    db: Session,
    submission_no: str,
    followup_date,
    followup_time: str,
    contact_person: str,
    notes: str | None,
    user_id: int | None,
) -> SubmissionFollowup:
    """Logs a call/visit made to the authority to check on a submission
    that's already been sent. The first follow-up against a freshly
    'Submitted' application also nudges it to 'Under Review' -- checking in
    on it is, in practice, what that status transition represents."""
    submission = get_submission(db, submission_no)
    if submission.status not in AWAITING_RESPONSE_STATUSES:
        raise ValidationAppError(
            "Follow-ups can only be recorded once the submission has been sent to the authority."
        )

    followup = SubmissionFollowup(
        submission_id=submission.id,
        followup_date=followup_date,
        followup_time=followup_time,
        contact_person=contact_person.strip(),
        notes=notes.strip() if notes and notes.strip() else None,
        created_by=user_id,
    )
    db.add(followup)

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Follow-up recorded", user_id, new_value=contact_person.strip()
    )
    db.commit()
    db.refresh(followup)

    if submission.status == "Submitted":
        set_status(db, submission_no, "Under Review", None, user_id)

    return followup


def _submission_exists(db: Session, submission_no: str) -> GovernmentSubmission:
    """Like get_submission() but doesn't exclude soft-deleted submissions
    -- used only for the read-only audit-trail view."""
    submission = db.query(GovernmentSubmission).filter(GovernmentSubmission.submission_no == submission_no).first()
    if submission is None:
        raise NotFoundError("Submission")
    return submission


def get_audit_events(db: Session, submission_no: str) -> list[dict]:
    submission = _submission_exists(db, submission_no)
    return audit_service.get_history(db, ENTITY_TYPE, submission.id)
