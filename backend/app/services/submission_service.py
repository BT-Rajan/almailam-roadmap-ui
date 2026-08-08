from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.status_transitions import (
    SUBMISSION_ALLOWED_TRANSITIONS,
    SUBMISSION_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.government import GovernmentSubmission, SubmissionDocument
from app.models.project import Project
from app.services import audit_service, government_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "GOVERNMENT_SUBMISSION"


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
    if form.authority_id != authority_id:
        raise ValidationAppError("formId does not belong to the given authorityId.")

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


def get_audit_events(db: Session, submission_no: str) -> list[dict]:
    submission = get_submission(db, submission_no)
    return audit_service.get_history(db, ENTITY_TYPE, submission.id)
