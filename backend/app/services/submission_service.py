from datetime import date, datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.status_transitions import SUBMISSION_ALLOWED_TRANSITIONS
from app.core.workflow import assert_transition_allowed
from app.models.client import Client
from app.models.government import GovernmentSubmission, SubmissionDocument, SubmissionFollowup
from app.models.project import Project
from app.models.user import User
from app.services import (
    audit_service,
    email_service,
    email_template_service,
    government_service,
    notification_service,
    permit_catalog_service,
    project_service,
    timeline_service,
)
from app.services.number_series_service import next_number

ENTITY_TYPE = "GOVERNMENT_SUBMISSION"
UPLOAD_SUBDIRECTORY = "submissions"

# Stages in which recording a follow-up with the authority makes sense --
# i.e. it's actually been filed (past Apply) and is awaiting a decision.
AWAITING_RESPONSE_STAGES = ("Track",)


def parse_followup_id(raw: str) -> int:
    """"FUP-0004" -> 4, same convention as client_service.parse_prefixed_id
    -- FollowupOut.id is formatted this way (see schemas/government.py),
    so the download route needs this to resolve it back to a real row."""
    text = raw.removeprefix("FUP-") if raw.upper().startswith("FUP-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid follow-up id.")
    return int(text)


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
    db: Session, project_no: str | None = None, stage: str | None = None
) -> list[GovernmentSubmission]:
    query = db.query(GovernmentSubmission).filter(GovernmentSubmission.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(GovernmentSubmission.project_id == (project.id if project else -1))
    if stage:
        query = query.filter(GovernmentSubmission.stage == stage)
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


def get_documents_by_submission(db: Session, submission_ids: list[int]) -> dict[int, list[SubmissionDocument]]:
    """Batched sibling of get_documents -- one query for every submission's
    documents instead of one query per submission. Used by list_submissions'
    _to_out_batch (see api/submissions.py) to avoid an N+1 there."""
    if not submission_ids:
        return {}
    documents = (
        db.query(SubmissionDocument)
        .filter(SubmissionDocument.submission_id.in_(submission_ids))
        .order_by(SubmissionDocument.id.asc())
        .all()
    )
    by_submission: dict[int, list[SubmissionDocument]] = {sid: [] for sid in submission_ids}
    for document in documents:
        by_submission[document.submission_id].append(document)
    return by_submission


def user_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Batched sibling of user_name -- one query for a whole set of user
    ids instead of one query per id. Callers still need their own
    None -> "System" handling, same as user_name(None)."""
    user_ids.discard(None)
    if not user_ids:
        return {}
    return {u.id: u.full_name for u in db.query(User).filter(User.id.in_(user_ids)).all()}


def _assert_no_open_application(db: Session, selected_permit_id: int) -> None:
    open_application = (
        db.query(GovernmentSubmission)
        .filter(
            GovernmentSubmission.project_selected_permit_id == selected_permit_id,
            GovernmentSubmission.stage != "Close",
            GovernmentSubmission.deleted_at.is_(None),
        )
        .first()
    )
    if open_application is not None:
        raise ConflictError(
            f"Permit application {open_application.submission_no} is already open for this permit."
        )


def create_submission(db: Session, payload, user_id: int | None) -> GovernmentSubmission:
    """Starts a new Permit Application in Prepare. Either the caller picks
    the authority/form (an ad hoc application), or -- sent with only a
    selectedPermitId -- the planned permit's own type decides the
    authority, form and checklist, so nothing is chosen and nothing can
    be mismatched. The rest of Prepare (filling the form in via ProjectFormEntry,
    getting the required-documents checklist ready, then
    confirm_readiness below) happens against this row afterward."""
    project = _parse_project_id_from_no(payload.projectId, db)

    selected_permit = None
    if getattr(payload, "selectedPermitId", None):
        if not payload.selectedPermitId.isdigit():
            raise ValidationAppError("selectedPermitId must be a valid id.")
        # Scoped to this same project -- 404s rather than silently
        # linking to another project's planned permit.
        selected_permit = project_service.get_selected_permit(db, project.id, int(payload.selectedPermitId))
    selected_permit_id = selected_permit.id if selected_permit else None

    documents_to_seed: list[str] | None = None
    started_from_permit = payload.authorityId is None and payload.formId is None
    if started_from_permit:
        # Started from a planned permit: its type's setup decides
        # everything (see permit_catalog_service.resolve_application_setup).
        if selected_permit is None:
            raise ValidationAppError("Choose an authority and a form, or start from a planned permit.")
        _assert_no_open_application(db, selected_permit.id)
        authority, form, documents_to_seed = permit_catalog_service.resolve_application_setup(
            db, selected_permit.permit_catalog_item_id
        )
        authority_id, form_id = authority.id, form.id
    elif payload.authorityId is None or payload.formId is None:
        raise ValidationAppError("Choose both an authority and a form.")
    else:
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
        project_selected_permit_id=selected_permit_id,
        expected_decision_date=payload.expectedDecisionDate,
        notes=payload.notes,
    )
    db.add(submission)
    db.flush()

    # Seed the per-application document checklist from the form's
    # required documents template -- each starts Pending until
    # uploaded/verified; this is what confirm_readiness's own check
    # waits on.
    # A permit type's own checklist, when it has one, replaces the form's.
    for document_name in documents_to_seed if documents_to_seed is not None else form.required_documents:
        db.add(SubmissionDocument(submission_id=submission.id, name=document_name, status="Pending"))

    # Starting an application from a planned permit is what "In Progress"
    # means for it -- no separate click, and no second place to keep in step.
    if started_from_permit and selected_permit.status in ("Planned", "Eligible"):
        previous_status = selected_permit.status
        selected_permit.status = "In Progress"
        audit_service.log_event(
            db, "PROJECT", project.id, "Permit status changed", user_id,
            previous_value=previous_status, new_value="In Progress",
        )

    audit_service.log_event(db, ENTITY_TYPE, submission.id, "Application created", user_id, new_value=submission.submission_no)
    timeline_service.create_system_event(
        db, project.id, "submission",
        title=f"Permit application {submission.submission_no} created",
        actor_id=user_id,
    )
    db.commit()
    db.refresh(submission)
    return submission


def update_submission(db: Session, submission_no: str, payload, user_id: int | None) -> GovernmentSubmission:
    """Edits an application's own details -- doesn't change its stage,
    that only ever happens through the dedicated stage-advancing actions
    below. A closed application is a finished record and can't be edited.
    Only the fields actually present in the request are applied."""
    submission = get_submission(db, submission_no)
    if submission.stage == "Close":
        raise ValidationAppError("A closed permit application can no longer be edited.")

    provided = payload.model_fields_set
    changes: dict[str, tuple] = {}

    if "expectedDecisionDate" in provided and payload.expectedDecisionDate != submission.expected_decision_date:
        changes["expected_decision_date"] = (submission.expected_decision_date, payload.expectedDecisionDate)
        submission.expected_decision_date = payload.expectedDecisionDate

    if "notes" in provided:
        new_notes = (payload.notes or "").strip() or None
        if new_notes != submission.notes:
            changes["notes"] = (submission.notes, new_notes)
            submission.notes = new_notes

    if "selectedPermitId" in provided:
        new_permit_id = None
        if payload.selectedPermitId:
            if not payload.selectedPermitId.isdigit():
                raise ValidationAppError("selectedPermitId must be a valid id.")
            # Scoped to this application's own project -- 404s rather than
            # silently linking to another project's planned permit.
            new_permit_id = project_service.get_selected_permit(
                db, submission.project_id, int(payload.selectedPermitId)
            ).id
        if new_permit_id != submission.project_selected_permit_id:
            changes["project_selected_permit_id"] = (submission.project_selected_permit_id, new_permit_id)
            submission.project_selected_permit_id = new_permit_id

    if "authorityId" in provided or "formId" in provided:
        new_authority_id = (
            government_service.parse_authority_id(payload.authorityId)
            if payload.authorityId is not None
            else submission.authority_id
        )
        new_form_id = (
            government_service.parse_form_id(payload.formId) if payload.formId is not None else submission.form_id
        )
        if (new_authority_id, new_form_id) != (submission.authority_id, submission.form_id):
            _change_authority_and_form(db, submission, new_authority_id, new_form_id, changes)

    audit_service.log_field_changes(db, ENTITY_TYPE, submission.id, changes, user_id)
    db.commit()
    db.refresh(submission)
    return submission


def _change_authority_and_form(
    db: Session, submission: GovernmentSubmission, authority_id: int, form_id: int, changes: dict[str, tuple]
) -> None:
    """Re-points an application at a different authority/form and
    re-seeds its required-documents checklist from the new form. Only
    allowed while nothing has been done against the old one -- still in
    Prepare, and no document uploaded/verified -- since the checklist
    (and anything filed) belongs to that form."""
    documents = get_documents(db, submission.id)
    if submission.stage != "Prepare" or any(d.status != "Pending" for d in documents):
        raise ValidationAppError(
            "The authority and form can only be changed while the application is still in Prepare and "
            "no required document has been uploaded. Delete this application and create a new one instead."
        )
    government_service.get_authority(db, authority_id)  # 404 if unknown
    form = government_service.get_form(db, form_id)
    if form.authority_id != authority_id:
        raise ValidationAppError("The selected form doesn't belong to the selected authority.")

    changes["authority_id"] = (submission.authority_id, authority_id)
    changes["form_id"] = (submission.form_id, form_id)
    submission.authority_id = authority_id
    submission.form_id = form_id

    db.query(SubmissionDocument).filter(SubmissionDocument.submission_id == submission.id).delete()
    for document_name in form.required_documents:
        db.add(SubmissionDocument(submission_id=submission.id, name=document_name, status="Pending"))


def delete_submission(db: Session, submission_no: str, user_id: int | None) -> None:
    """Soft-deletes a permit application -- it disappears from every list,
    search and report (they all filter on deleted_at), while its audit
    trail stays readable. The planned permit it was linked to and the
    project's filled-in forms are left alone."""
    submission = get_submission(db, submission_no)
    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Application deleted", user_id, previous_value=submission.submission_no
    )
    timeline_service.create_system_event(
        db, submission.project_id, "submission",
        title=f"Permit application {submission.submission_no} deleted",
        actor_id=user_id,
    )
    submission.deleted_at = datetime.now(timezone.utc)
    db.commit()


def _set_stage(db: Session, submission: GovernmentSubmission, new_stage: str, user_id: int | None) -> None:
    """Internal transition helper -- every public stage-advancing action
    below (confirm_readiness / record_acknowledgement / add_followup /
    close_application) goes through this rather than exposing a bare
    "set stage" endpoint, since each of those already carries whatever
    data that transition actually needs (a readiness confirmation, an
    acknowledgement, a follow-up entry, a closing outcome) -- there's no
    stage change in this workflow that isn't also one of those. Does not
    commit; the caller's own action does that as part of one
    transaction, same convention as project_service._apply_stage_change.
    """
    if new_stage == submission.stage:
        return
    assert_transition_allowed(SUBMISSION_ALLOWED_TRANSITIONS, submission.stage, new_stage, "submission")
    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Stage changed", user_id,
        previous_value=submission.stage, new_value=new_stage,
    )
    submission.stage = new_stage


def set_document_status(
    db: Session, submission_no: str, document_id: int, new_status: str
) -> SubmissionDocument:
    submission = get_submission(db, submission_no)
    document = _get_document(db, submission, document_id)
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
    entry -- only while the application is still in Prepare, matching
    the "fill each one in as it becomes available, then confirm
    readiness" flow."""
    submission = get_submission(db, submission_no)
    if submission.stage != "Prepare":
        raise ValidationAppError("Required documents can only be updated while the application is in Prepare.")
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


def confirm_readiness(db: Session, submission_no: str, user_id: int | None) -> GovernmentSubmission:
    """Closes out Prepare and moves the application into Apply -- gated
    on every required document already being Uploaded/Verified, same
    bar the old Draft -> Submitted transition always used."""
    submission = get_submission(db, submission_no)
    if submission.stage != "Prepare":
        raise ValidationAppError("Readiness can only be confirmed while the application is in Prepare.")
    documents = get_documents(db, submission.id)
    if not all_documents_satisfied(documents):
        missing = [d.name for d in documents if d.status not in ("Uploaded", "Verified")]
        raise ValidationAppError(
            f"Cannot confirm readiness -- these required documents are still pending: {', '.join(missing)}."
        )

    submission.readiness_confirmed_at = date.today()
    submission.readiness_confirmed_by = user_id
    _set_stage(db, submission, "Apply", user_id)

    db.commit()
    db.refresh(submission)
    return submission


def record_acknowledgement(
    db: Session,
    submission_no: str,
    file: UploadFile | None,
    acknowledgement_number: str | None,
    payment_reference: str | None,
    notes: str | None,
    user_id: int | None,
) -> GovernmentSubmission:
    """Files the application -- records the authority's acknowledgement
    (number, date, an optional payment reference, and the acknowledgement
    document itself) and moves Apply -> Track. Mirrors the old Draft ->
    Submitted transition's role, just carrying more of what actually
    happens at that moment instead of a bare file upload."""
    submission = get_submission(db, submission_no)
    if submission.stage != "Apply":
        raise ValidationAppError("An acknowledgement can only be recorded while the application is in Apply.")

    if file is not None:
        storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)
        submission.proof_of_submission_storage_key = storage_key
        submission.proof_of_submission_filename = original_filename
        submission.proof_of_submission_size_bytes = size_bytes
        submission.proof_of_submission_uploaded_by = user_id
        submission.proof_of_submission_upload_date = date.today()

    submission.acknowledgement_number = acknowledgement_number.strip() if acknowledgement_number else None
    submission.payment_reference = payment_reference.strip() if payment_reference else None
    if notes:
        submission.notes = notes.strip()
    submission.submitted_date = date.today()

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Acknowledgement recorded", user_id, new_value=submission.acknowledgement_number
    )
    _set_stage(db, submission, "Track", user_id)
    db.commit()
    db.refresh(submission)

    _send_permit_fyi_email(db, submission, "permit_application_submitted", {})
    return submission


def get_proof_of_submission_download_target(db: Session, submission_no: str):
    submission = get_submission(db, submission_no)
    if submission.proof_of_submission_storage_key is None:
        raise NotFoundError("Acknowledgement document")
    return resolve_path(submission.proof_of_submission_storage_key), submission.proof_of_submission_filename


def get_proof_of_response_download_target(db: Session, submission_no: str):
    submission = get_submission(db, submission_no)
    if submission.proof_of_response_storage_key is None:
        raise NotFoundError("Permit/decision document")
    return resolve_path(submission.proof_of_response_storage_key), submission.proof_of_response_filename


def close_application(
    db: Session,
    submission_no: str,
    outcome: str,
    closing_notes: str,
    file: UploadFile | None,
    user_id: int | None,
) -> GovernmentSubmission:
    """Closes the application out -- records the final outcome, an
    optional permit/decision document (there's often nothing to attach
    for a Withdrawn/No Response outcome), and closing notes. Reachable
    from any stage (see SUBMISSION_ALLOWED_TRANSITIONS), not only
    Track, so an application can be withdrawn before it's even filed.

    An Approved outcome is exactly what project_service's Government
    Submission -> Supervision exit criterion cares about -- flush first
    so that check's own fresh query sees this row's new stage/outcome
    (session is autoflush=False), then let the same auto-advance path
    every other stage-completing action goes through pick it up.
    """
    submission = get_submission(db, submission_no)

    if file is not None:
        storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)
        submission.proof_of_response_storage_key = storage_key
        submission.proof_of_response_filename = original_filename
        submission.proof_of_response_size_bytes = size_bytes
        submission.proof_of_response_uploaded_by = user_id
        submission.proof_of_response_upload_date = date.today()

    submission.response_outcome = outcome
    submission.closing_notes = closing_notes.strip()
    submission.decision_date = date.today()

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Application closed", user_id, new_value=outcome, reason=closing_notes
    )
    _set_stage(db, submission, "Close", user_id)

    if outcome == "Approved":
        db.flush()
        project = db.query(Project).filter(Project.id == submission.project_id).first()
        if project is not None:
            project_service.try_auto_advance_stage(db, project, user_id)

    db.commit()
    db.refresh(submission)

    _send_permit_fyi_email(db, submission, "permit_response_received", {"decision": outcome})
    return submission


def _send_permit_fyi_email(
    db: Session, submission: GovernmentSubmission, template_key: str, extra_context: dict[str, str]
) -> None:
    """Informational-only email to the client for a permit application
    milestone (filed / decision received) -- never OTP-gated, same
    "for your information" category as quotation_approved/
    contract_signed, gated the same way on client.email_consent. Runs
    after the caller's own commit, in its own try/except, so a delivery
    failure only notifies Administrators (same pattern as those two)
    rather than unwinding the stage change that already succeeded."""
    project = db.query(Project).filter(Project.id == submission.project_id).first()
    if project is None:
        return
    client = db.query(Client).filter(Client.id == project.client_id).first()
    if client is None or not client.email_consent:
        return

    authority = government_service.get_authority(db, submission.authority_id)
    form = government_service.get_form(db, submission.form_id)

    try:
        subject, body = email_template_service.render(
            db, template_key,
            {
                "contact_person": client.contact_person,
                "form_title": form.title,
                "authority_name": authority.name,
                "project_name": project.project_name,
                "project_no": project.project_no,
                "submission_no": submission.submission_no,
                "submitted_date": submission.submitted_date.isoformat() if submission.submitted_date else "",
                "decision_date": submission.decision_date.isoformat() if submission.decision_date else "",
                **extra_context,
            },
        )
        email_service.send_email(client.email, subject, body, db=db)
    except ValidationAppError as error:
        notification_service.notify_role(
            db, "Administrator",
            "Permit notification email not sent",
            f"Application {submission.submission_no} for {project.project_no} reached '{submission.stage}', "
            f"but the notification email to the client could not be sent: {error}",
            "System",
            link_route_name="project-workspace", link_params={"projectId": project.project_no},
            link_query={"tab": "government"},
        )
        db.commit()


def get_followups(db: Session, submission_id: int) -> list[SubmissionFollowup]:
    return (
        db.query(SubmissionFollowup)
        .filter(SubmissionFollowup.submission_id == submission_id)
        .order_by(SubmissionFollowup.created_at.desc(), SubmissionFollowup.id.desc())
        .all()
    )


def get_followup_document_download_target(db: Session, submission_no: str, followup_id: int):
    submission = get_submission(db, submission_no)
    followup = (
        db.query(SubmissionFollowup)
        .filter(SubmissionFollowup.id == followup_id, SubmissionFollowup.submission_id == submission.id)
        .first()
    )
    if followup is None or followup.storage_key is None:
        raise NotFoundError("Follow-up document")
    return resolve_path(followup.storage_key), followup.original_filename


def add_followup(
    db: Session,
    submission_no: str,
    followup_date,
    followup_time: str,
    contact_person: str,
    notes: str | None,
    file: UploadFile | None,
    user_id: int | None,
) -> SubmissionFollowup:
    """Records a follow-up made with the authority while the application is in
    Track -- a plain check-in, or one that also carries a document (an
    additional document the authority asked for, or an updated version
    of one already sent). Doesn't move the application: it stays in
    Track until it's closed."""
    submission = get_submission(db, submission_no)
    if submission.stage not in AWAITING_RESPONSE_STAGES:
        raise ValidationAppError("A follow-up can only be recorded once the application has been filed (Track).")

    storage_key = original_filename = None
    size_bytes = None
    if file is not None:
        storage_key, original_filename, size_bytes = save_upload(file, UPLOAD_SUBDIRECTORY)

    followup = SubmissionFollowup(
        submission_id=submission.id,
        followup_date=followup_date,
        followup_time=followup_time,
        contact_person=contact_person.strip(),
        notes=notes.strip() if notes and notes.strip() else None,
        storage_key=storage_key,
        original_filename=original_filename,
        file_size_bytes=size_bytes,
        created_by=user_id,
    )
    db.add(followup)

    audit_service.log_event(
        db, ENTITY_TYPE, submission.id, "Follow-up recorded", user_id, new_value=contact_person.strip()
    )
    db.commit()
    db.refresh(followup)
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
