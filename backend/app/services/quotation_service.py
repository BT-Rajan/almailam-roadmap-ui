from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import assert_pdf_upload
from app.core.status_transitions import (
    QUOTATION_ALLOWED_TRANSITIONS,
    QUOTATION_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.client import Client
from app.models.payment import AGREEMENT_STREAMS
from app.models.project import Project, ProjectScopeRevision
from app.models.quotation import Quotation, QuotationLineItem, QuotationRevision
from app.models.user import User
from app.services import audit_service, document_service, document_template_service, email_service, email_template_service, notification_service, payment_service, project_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "QUOTATION"


def compute_amount(line_items: list[tuple], discount_amount) -> Decimal:
    """line_items: iterable of (quantity, unit_price) pairs."""
    subtotal = sum(
        (Decimal(str(quantity)) * Decimal(str(unit_price)) for quantity, unit_price in line_items),
        Decimal("0"),
    )
    return (subtotal - Decimal(str(discount_amount))).quantize(Decimal("0.01"))


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def _assert_valid_client(db: Session, project: Project) -> None:
    """A project's client_id is a NOT NULL FK, so a project can never be
    created without pointing at some client row -- but that row can
    still have been soft-deleted since. Block quotation creation in
    that case so nothing gets generated against a client record that
    is no longer valid."""
    client = db.query(Client).filter(Client.id == project.client_id, Client.deleted_at.is_(None)).first()
    if client is None:
        raise ValidationAppError(
            "This project's client record is missing or has been removed. "
            "A quotation cannot be created without a valid client."
        )


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _next_revision_label(current: str) -> str:
    # Revision labels are 'R0', 'R1', 'R2', ... -- bump the numeric suffix.
    if current.startswith("R") and current[1:].isdigit():
        return f"R{int(current[1:]) + 1}"
    return "R1"


def _record_revision(db: Session, quotation: Quotation, summary: str, user_id: int, *, bump: bool) -> None:
    """Writes one quotation_revisions row. bump=True (every content save
    after the first) also advances quotation.revision itself; the very
    first row (written at creation) keeps the quotation at its starting
    'R0' label since nothing has changed yet at that point."""
    new_label = _next_revision_label(quotation.revision) if bump else quotation.revision
    db.add(
        QuotationRevision(
            quotation_id=quotation.id, revision=new_label, revised_at=date.today(),
            changed_by=user_id, summary=summary,
        )
    )
    if bump:
        quotation.revision = new_label


def list_quotations(db: Session, project_no: str | None = None, status: str | None = None) -> list[Quotation]:
    query = db.query(Quotation).filter(Quotation.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(Quotation.project_id == (project.id if project else -1))
    if status:
        query = query.filter(Quotation.status == status)
    return query.order_by(Quotation.id.asc()).all()


def get_quotation(db: Session, quotation_no: str) -> Quotation:
    quotation = (
        db.query(Quotation)
        .filter(Quotation.quotation_no == quotation_no, Quotation.deleted_at.is_(None))
        .first()
    )
    if quotation is None:
        raise NotFoundError("Quotation")
    return quotation


def get_revisions_with_names(db: Session, quotation_id: int) -> list[tuple]:
    revisions = (
        db.query(QuotationRevision)
        .filter(QuotationRevision.quotation_id == quotation_id)
        .order_by(QuotationRevision.id.desc())
        .all()
    )
    # Batched, same reasoning as contract_service.get_revisions_with_names.
    changed_by_ids = {r.changed_by for r in revisions}
    names = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(changed_by_ids)).all()}
    return [(r, names.get(r.changed_by, "Unknown")) for r in revisions]


def get_revisions_with_names_by_quotation(db: Session, quotation_ids: list[int]) -> dict[int, list[tuple]]:
    """Batched sibling of get_revisions_with_names -- one query for every
    quotation's revisions and one for all their authors, instead of a
    per-quotation (and, before the fix above, per-revision) query. Used
    by list_quotations' _to_out_batch (see api/quotations.py)."""
    if not quotation_ids:
        return {}
    revisions = (
        db.query(QuotationRevision)
        .filter(QuotationRevision.quotation_id.in_(quotation_ids))
        .order_by(QuotationRevision.id.desc())
        .all()
    )
    changed_by_ids = {r.changed_by for r in revisions}
    names = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(changed_by_ids)).all()}
    by_quotation: dict[int, list[tuple]] = {qid: [] for qid in quotation_ids}
    for revision in revisions:
        by_quotation[revision.quotation_id].append((revision, names.get(revision.changed_by, "Unknown")))
    return by_quotation


def get_line_items(db: Session, quotation_id: int) -> list[QuotationLineItem]:
    return (
        db.query(QuotationLineItem)
        .filter(QuotationLineItem.quotation_id == quotation_id)
        .order_by(QuotationLineItem.id.asc())
        .all()
    )


def get_line_items_by_quotation(db: Session, quotation_ids: list[int]) -> dict[int, list[QuotationLineItem]]:
    """Batched sibling of get_line_items -- one query for every
    quotation's line items instead of one query per quotation."""
    if not quotation_ids:
        return {}
    items = (
        db.query(QuotationLineItem)
        .filter(QuotationLineItem.quotation_id.in_(quotation_ids))
        .order_by(QuotationLineItem.id.asc())
        .all()
    )
    by_quotation: dict[int, list[QuotationLineItem]] = {qid: [] for qid in quotation_ids}
    for item in items:
        by_quotation[item.quotation_id].append(item)
    return by_quotation


def create_quotation(db: Session, payload, user_id: int) -> Quotation:
    project = _project_by_no(db, payload.projectId)
    _assert_valid_client(db, project)
    project_service.assert_project_open_for_new_work(project)
    amount = compute_amount([(item.quantity, item.unitPrice) for item in payload.lineItems], payload.discountAmount)
    if amount < 0:
        # discountAmount only has a >= 0 floor at the schema level
        # (QuotationCreate) -- nothing there can also check it against
        # the line items' own subtotal, since Pydantic validates each
        # payload in isolation. A discount larger than the subtotal
        # would otherwise silently produce a negative quotation total,
        # which is meaningless on a real document sent to a client and
        # would carry through to whatever Contract/Payment Plan gets
        # built from this amount later.
        raise ValidationAppError(
            f"The discount ({payload.discountAmount:.2f} {payload.currency}) cannot be more than the line items subtotal."
        )

    # Not blocked -- staff sometimes do legitimately need another
    # quotation once one's already Approved (a scope change mid-project,
    # say) -- but it's unusual enough, and easy enough to do by accident
    # while looking at an old Draft/Rejected/Expired sibling, that
    # Administrators should know it happened rather than the project
    # quietly ending up with two "live-looking" quotations.
    existing_approved = (
        db.query(Quotation)
        .filter(Quotation.project_id == project.id, Quotation.status == "Approved")
        .first()
    )

    quotation = Quotation(
        quotation_no=next_number(db, "QUOTATION"),
        project_id=project.id,
        issue_date=date.today(),
        validity=payload.validity,
        currency=payload.currency,
        prepared_by=user_id,
        discount_amount=payload.discountAmount,
        notes=payload.notes,
        terms_and_conditions=payload.termsAndConditions,
        scope_phases=payload.scopePhases,
        payment_terms=payload.paymentTerms,
        amount=amount,
    )
    db.add(quotation)
    db.flush()

    for item in payload.lineItems:
        db.add(
            QuotationLineItem(
                quotation_id=quotation.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unitPrice,
            )
        )

    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation created", user_id, new_value=quotation.quotation_no)
    timeline_service.create_system_event(
        db, project.id, "quotation",
        title=f"Quotation {quotation.quotation_no} created",
        actor_id=user_id,
    )
    # First revision history entry, written automatically -- not just on
    # every later save, but from the very first time the quotation exists.
    _record_revision(db, quotation, "Initial quotation created", user_id, bump=False)
    # Safety-net catch-up call -- "Requirement" -> "Quotation" no longer
    # depends on a quotation existing (it waits on scope-of-work approval
    # + client identification instead, see project_service._assert_
    # stage_exit_criteria), but this is still a moment those could
    # coincidentally already both be true without anything else having
    # triggered the move yet. No-op otherwise.
    db.flush()
    project_service.try_auto_advance_stage(db, project, user_id)

    if existing_approved is not None:
        notification_service.notify_role(
            db, "Administrator",
            "Quotation created while one is already Approved",
            f"Quotation {quotation.quotation_no} was created for project {project.project_no}, "
            f"which already has an Approved quotation ({existing_approved.quotation_no}). "
            "Confirm this was intentional.",
            "Project",
            link_route_name="project-workspace",
            link_params={"projectId": project.project_no},
            link_query={"tab": "quotation"},
        )

    db.commit()
    db.refresh(quotation)
    return quotation


_QUOTATION_CONTENT_FIELDS = (
    "validity", "discountAmount", "notes", "termsAndConditions", "scopePhases", "paymentTerms", "lineItems",
)


def update_quotation(db: Session, quotation_no: str, payload, user_id: int) -> Quotation:
    quotation = get_quotation(db, quotation_no)
    # The finalize lock only protects document *content* -- status moves
    # (Send/Approve/Reject) stay allowed on a finalized quotation, since
    # finalizing is what makes it ready to send in the first place.
    touches_content = any(getattr(payload, field, None) is not None for field in _QUOTATION_CONTENT_FIELDS)
    if quotation.finalized_at is not None and touches_content:
        raise ValidationAppError(
            "This quotation has been finalized and its content is locked. Reopen it first to make changes."
        )
    changes: dict[str, tuple] = {}

    if payload.validity is not None and payload.validity != quotation.validity:
        changes["validity"] = (quotation.validity, payload.validity)
        quotation.validity = payload.validity
    if payload.notes is not None and payload.notes != quotation.notes:
        changes["notes"] = (quotation.notes, payload.notes)
        quotation.notes = payload.notes
    if payload.termsAndConditions is not None:
        quotation.terms_and_conditions = payload.termsAndConditions
    if payload.scopePhases is not None:
        quotation.scope_phases = payload.scopePhases
    if payload.paymentTerms is not None:
        quotation.payment_terms = payload.paymentTerms

    discount = payload.discountAmount if payload.discountAmount is not None else quotation.discount_amount
    if payload.discountAmount is not None:
        changes["discount_amount"] = (quotation.discount_amount, payload.discountAmount)
        quotation.discount_amount = payload.discountAmount

    if payload.lineItems is not None:
        db.query(QuotationLineItem).filter(QuotationLineItem.quotation_id == quotation.id).delete()
        for item in payload.lineItems:
            db.add(
                QuotationLineItem(
                    quotation_id=quotation.id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unitPrice,
                )
            )
        line_items_for_calc = [(item.quantity, item.unitPrice) for item in payload.lineItems]
    else:
        line_items_for_calc = [
            (float(i.quantity), float(i.unit_price)) for i in get_line_items(db, quotation.id)
        ]

    new_amount = compute_amount(line_items_for_calc, discount)
    if new_amount < 0:
        # Same subtotal-vs-discount guard as create_quotation -- payload
        # validation alone can't catch this here either, since discount
        # and line items can be edited independently of each other (see
        # QuotationUpdate: both optional) and the check needs whichever
        # one wasn't sent in this particular request, from the DB.
        raise ValidationAppError(
            f"The discount ({discount:.2f} {quotation.currency}) cannot be more than the line items subtotal."
        )
    if new_amount != quotation.amount:
        changes["amount"] = (quotation.amount, new_amount)
        quotation.amount = new_amount

    audit_service.log_field_changes(db, ENTITY_TYPE, quotation.id, changes, user_id)

    # Every save that actually changes content gets its own revision
    # history entry (line items are content too, even though they don't
    # go through the `changes` dict above since they're a separate table).
    if changes or payload.lineItems is not None:
        summary = "Line items updated" if not changes else "Updated " + ", ".join(sorted(changes.keys()))
        if changes and payload.lineItems is not None:
            summary += " and line items"
        _record_revision(db, quotation, summary, user_id, bump=True)

    db.commit()
    db.refresh(quotation)

    if payload.status is not None and payload.status != quotation.status:
        quotation = set_status(db, quotation_no, payload.status, payload.reason, user_id)

    return quotation


_STATUS_CHANGE_LABELS = {
    "Approved": "Quotation approved",
    "Rejected": "Quotation rejected",
    "Expired": "Quotation expired",
    "Draft": "Quotation moved back to Draft",
}


def set_status(db: Session, quotation_no: str, new_status: str, reason: str | None, user_id: int | None) -> Quotation:
    quotation = get_quotation(db, quotation_no)
    assert_transition_allowed(QUOTATION_ALLOWED_TRANSITIONS, quotation.status, new_status, "quotation")
    if new_status in QUOTATION_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the quotation to '{new_status}'.")

    # A quotation can only leave Draft once its content is locked -- the
    # client shouldn't be asked to approve something that's still an
    # editable work-in-progress. finalize_quotation()/"Save as Final" is
    # how it gets locked.
    if quotation.status == "Draft" and new_status != "Draft" and quotation.finalized_at is None:
        raise ValidationAppError(
            "Save the quotation as Final before moving it out of Draft -- "
            "its content needs to be locked before a decision is recorded on it."
        )

    # A specific, human-readable label per target status (rather than one
    # generic "Status changed") is what makes get_audit_events/the
    # frontend's quotation history read as a real timeline -- "Quotation
    # approved" / "Quotation rejected" / "Quotation expired" / "Quotation
    # moved back to Draft" -- instead of everything saying the same thing
    # with the actual meaning buried in previous_value/new_value.
    audit_service.log_event(
        db, ENTITY_TYPE, quotation.id, _STATUS_CHANGE_LABELS.get(new_status, "Status changed"), user_id,
        previous_value=quotation.status, new_value=new_status, reason=reason,
    )
    quotation.status = new_status
    # Moving back to Draft (from Rejected or Expired) always reopens the
    # content for editing again. This is the other half of the rule
    # above: status == 'Draft' and locked content are mutually
    # exclusive, so a quotation is never shown as both "Draft" and
    # "Final" at once -- whichever way it got there.
    if new_status == "Draft" and quotation.finalized_at is not None:
        quotation.finalized_at = None
        audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation reopened for editing", user_id)
    if new_status == "Approved":
        # An Approved quotation is exactly what _assert_stage_exit_criteria
        # requires before a project can enter "Contract" -- advance it
        # automatically instead of requiring a separate manual stage
        # click for a condition this action already satisfied. The
        # session is autoflush=False -- flush first so the exit-criteria
        # check's own fresh query for an Approved quotation actually
        # sees this status change rather than the pre-change ("Draft")
        # value still on file.
        db.flush()
        project = db.query(Project).filter(Project.id == quotation.project_id).first()
        if project is not None:
            project_service.try_auto_advance_stage(db, project, user_id)
    db.commit()
    db.refresh(quotation)
    return quotation


def finalize_quotation(db: Session, quotation_no: str, user_id: int) -> Quotation:
    """Move a quotation from Draft (editable) to Final (locked,
    print-ready) -- required before it can be sent (see set_status).
    No-op guard against double-finalizing; reopen_quotation is the only
    way back to editable, and only while still in Draft status."""
    quotation = get_quotation(db, quotation_no)
    if quotation.finalized_at is not None:
        return quotation
    quotation.finalized_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation finalized", user_id)
    db.commit()
    db.refresh(quotation)
    return quotation


def reopen_quotation(db: Session, quotation_no: str, user_id: int) -> Quotation:
    """Unlock a finalized quotation for further editing. Only
    allowed while status is still 'Draft' -- once a decision has been
    recorded on it, its locked content can't be silently pulled back
    into an editable state (move it back to Draft via Rejected/Expired
    first, which reopens it automatically -- see set_status)."""
    quotation = get_quotation(db, quotation_no)
    if quotation.status != "Draft":
        raise ValidationAppError(
            f"Only a quotation still in Draft status can be reopened for editing (currently '{quotation.status}')."
        )
    quotation.finalized_at = None
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation reopened for editing", user_id)
    db.commit()
    db.refresh(quotation)
    return quotation


def _quotation_breakdown_text(quotation: Quotation, line_items: list[QuotationLineItem]) -> str:
    lines = [f"{item.description}: {item.quantity} x {item.unit_price:.2f} {quotation.currency} "
             f"= {(Decimal(str(item.quantity)) * Decimal(str(item.unit_price))):.2f} {quotation.currency}"
             for item in line_items]
    lines.append(f"Discount: {quotation.discount_amount:.2f} {quotation.currency}")
    lines.append(f"Total: {quotation.amount:.2f} {quotation.currency}")
    return "\n".join(lines)


def _payment_plan_summary_text(db: Session, project: Project) -> str:
    sections: list[str] = []
    for stream in AGREEMENT_STREAMS:
        agreement = payment_service.get_agreement_by_project(db, project.project_no, stream)
        if agreement is None:
            continue
        obligations = payment_service.get_obligations(db, agreement.id)
        lines = [
            f"{stream} -- {agreement.contract_amount:.2f} {agreement.currency}, "
            f"{agreement.payment_frequency}, status: {agreement.status}",
        ]
        lines.extend(
            f"  - {o.description}: {o.amount_due:.2f} {agreement.currency} due {o.due_date.isoformat()}"
            for o in obligations
        )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def confirm_quotation_approval(db: Session, quotation_no: str, file: UploadFile, user_id: int) -> Quotation:
    """Records the client's acceptance of the quotation -- previously an
    email OTP the client read back to staff, now a scan of their
    physically signed copy, uploaded here as the approval record (see
    document_service.create_document; stored as a "Quotation"-typed
    project Document, same as the generated copy staff can already
    email out). There's no code to verify, so this is a direct manual
    action (any Draft+finalized quotation can be marked Approved this
    way) rather than a hard-gated one -- the signed upload is the
    evidence, not a cryptographic proof. Reuses set_status, which
    already triggers project_service.try_auto_advance_stage.

    If the project's scope of work hasn't been reconfirmed by the
    client since it was last edited (project.scope_client_confirmed_at
    is None -- see project_service.save_scope_of_work, which clears it
    on every edit), this same confirmation also serves as that
    reconfirmation: one signed document covers a scope change made
    mid-negotiation instead of requiring a separate round through the
    Requirement stage's own confirmation. Either way, the client is
    emailed a copy of the accepted quotation (PDF attached), always
    with its breakdown and a Payment Plan summary when one exists, and
    with a "what changed in the scope" section only when this call also
    just reconfirmed it.
    """
    quotation = get_quotation(db, quotation_no)
    if quotation.status != "Draft" or quotation.finalized_at is None:
        raise ValidationAppError("This quotation isn't awaiting approval.")
    assert_pdf_upload(file)

    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    if project is None:
        raise ValidationAppError("This quotation's project record is missing.")

    document_service.create_document(
        db, project.project_no, f"Signed Quotation {quotation.quotation_no}", "Quotation", file, user_id,
    )
    # Its own history line, distinct from the "Quotation approved" one
    # set_status logs right below -- the upload and the approval happen
    # together here, but they're still two separate facts worth being
    # able to see separately in the quotation's history (e.g. who
    # uploaded the file vs. whose action counted as the approval, if
    # that were ever to diverge).
    audit_service.log_event(
        db, ENTITY_TYPE, quotation.id, "Approval document uploaded", user_id, new_value=file.filename,
    )

    quotation = set_status(db, quotation_no, "Approved", None, user_id)

    notification_service.notify_role(
        db, "Administrator",
        "Quotation approved",
        f"Quotation {quotation.quotation_no} was approved -- confirmed via a signed document upload.",
        "System",
        link_route_name="project-workspace",
        link_params={"projectId": project.project_no},
        link_query={"tab": "quotation"},
    )
    db.commit()

    scope_was_reconfirmed = project.scope_client_confirmed_at is None
    if scope_was_reconfirmed:
        project.scope_client_confirmed_at = datetime.now(timezone.utc)
        audit_service.log_event(
            db, "PROJECT", project.id, "Scope of work confirmed via quotation approval", user_id
        )
        timeline_service.create_system_event(
            db, project.id, "note", title="Scope of work confirmed by client", description=project.description, actor_id=user_id,
        )
        db.flush()
        project_service.try_auto_advance_stage(db, project, user_id)
        db.commit()
        db.refresh(project)

    client = db.query(Client).filter(Client.id == project.client_id).first()
    if client is None or not client.email_consent:
        return quotation

    try:
        line_items = get_line_items(db, quotation.id)

        scope_change_section = ""
        if scope_was_reconfirmed:
            latest_revision = (
                db.query(ProjectScopeRevision)
                .filter(ProjectScopeRevision.project_id == project.id)
                .order_by(ProjectScopeRevision.id.desc())
                .first()
            )
            scope_change_section = (
                "The scope of work was also updated as part of this approval"
                + (f" ({latest_revision.summary})" if latest_revision else "")
                + f":\n{project.description}\n\n"
            )

        payment_plan_text = _payment_plan_summary_text(db, project)
        payment_plan_section = f"Payment plan:\n{payment_plan_text}\n\n" if payment_plan_text else ""

        subject, body = email_template_service.render(
            db,
            "quotation_approved",
            {
                "contact_person": client.contact_person,
                "quotation_no": quotation.quotation_no,
                "breakdown": _quotation_breakdown_text(quotation, line_items),
                "scope_change_section": scope_change_section,
                "payment_plan_section": payment_plan_section,
            },
        )

        content, filename = document_template_service.render_quotation_pdf(db, quotation, None)
        email_service.send_document_email(
            to_email=client.email,
            subject=subject,
            body_text=body,
            attachment_bytes=content,
            attachment_filename=filename,
            attachment_mimetype="application/pdf",
            db=db,
        )
    except ValidationAppError as error:
        # Most commonly: no default Quotation document template has
        # been uploaded yet (Administration > Documents), so there was
        # nothing to attach. Silently dropping this left staff with no
        # way to know the client was never actually emailed -- the
        # approval itself has already succeeded above and stays that
        # way; this only surfaces that the follow-up email didn't go
        # out, so someone can fix the template and use the quotation's
        # own "Email document" action to send it once it's fixed.
        notification_service.notify_role(
            db, "Administrator",
            "Quotation confirmation email not sent",
            f"Quotation {quotation.quotation_no} was approved, but the confirmation email to the client could not be sent: {error}",
            "System",
            link_route_name="project-workspace",
            link_params={"projectId": project.project_no},
            link_query={"tab": "quotation"},
        )
        db.commit()
    return quotation


def record_document_activity(db: Session, quotation_no: str, action_label: str, user_id: int, detail: str | None = None) -> None:
    """Logs a document-lifecycle event -- emailed, downloaded, printed --
    that isn't itself a content edit or a status move, so the quotation's
    history shows what actually happened to it end-to-end (who sent it,
    when it was pulled down, not just when its status changed)."""
    quotation = get_quotation(db, quotation_no)
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, action_label, user_id, new_value=detail)
    db.commit()


def check_and_expire_quotations(db: Session) -> int:
    """Finds finalized Draft quotations whose validity date has passed
    and moves them to Expired automatically -- the same transition
    staff can already make manually from the status menu, just applied
    the moment the deadline for a decision actually lapses instead of
    only when someone happens to notice.

    Only finalized quotations are eligible: set_status already refuses
    to move an unfinalized Draft out of Draft (see its own guard), so a
    quotation that was never actually finalized/sent is left alone even
    with a stale validity date -- it was never really "offered" to
    begin with, and a plain edit fixes the date whenever someone gets
    back to it.

    Called daily by the background scheduler (see main.py's lifespan),
    same shape as the other check_and_notify_* functions elsewhere in
    the codebase. Returns how many quotations were expired in this run.
    """
    today = date.today()
    candidates = (
        db.query(Quotation)
        .filter(
            Quotation.deleted_at.is_(None),
            Quotation.status == "Draft",
            Quotation.finalized_at.isnot(None),
            Quotation.validity < today,
        )
        .all()
    )

    expired_count = 0
    for quotation in candidates:
        # Skips a soft-deleted project's own quotations entirely -- no
        # status flip, no admin notification. See project_service.
        # delete_project's docstring: a deleted project should generate
        # no further tracking activity at all, not even this kind.
        project = (
            db.query(Project)
            .filter(Project.id == quotation.project_id, Project.deleted_at.is_(None))
            .first()
        )
        if project is None:
            continue
        quotation_no = quotation.quotation_no
        validity = quotation.validity
        set_status(db, quotation_no, "Expired", "Automatically expired: validity date passed.", None)
        notification_service.notify_role(
            db, "Administrator",
            "Quotation expired",
            f"Quotation {quotation_no} for project {project.project_no} passed its validity date "
            f"({validity.isoformat()}) without a decision and was automatically marked Expired.",
            "Project",
            link_route_name="project-workspace",
            link_params={"projectId": project.project_no},
            link_query={"tab": "quotation"},
        )
        db.commit()
        expired_count += 1
    return expired_count


def _quotation_exists(db: Session, quotation_no: str) -> Quotation:
    """Like get_quotation() but doesn't exclude soft-deleted quotations --
    used only for the read-only audit-trail view, so a deleted
    quotation's own history stays inspectable."""
    quotation = db.query(Quotation).filter(Quotation.quotation_no == quotation_no).first()
    if quotation is None:
        raise NotFoundError("Quotation")
    return quotation


def get_audit_events(db: Session, quotation_no: str) -> list[dict]:
    quotation = _quotation_exists(db, quotation_no)
    return audit_service.get_history(db, ENTITY_TYPE, quotation.id)


def delete_quotation(db: Session, quotation_no: str, actor_id: int) -> None:
    quotation = get_quotation(db, quotation_no)
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation deleted", actor_id, previous_value=quotation.quotation_no)
    quotation.deleted_at = datetime.now(timezone.utc)
    db.commit()
