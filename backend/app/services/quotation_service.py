from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import otp
from app.core.exceptions import NotFoundError, ValidationAppError
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
from app.services import audit_service, document_template_service, email_service, email_template_service, notification_service, payment_service, project_service, timeline_service
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
    return [(r, _user_name(db, r.changed_by)) for r in revisions]


def get_line_items(db: Session, quotation_id: int) -> list[QuotationLineItem]:
    return (
        db.query(QuotationLineItem)
        .filter(QuotationLineItem.quotation_id == quotation_id)
        .order_by(QuotationLineItem.id.asc())
        .all()
    )


def create_quotation(db: Session, payload, user_id: int) -> Quotation:
    project = _project_by_no(db, payload.projectId)
    _assert_valid_client(db, project)
    project_service.assert_project_open_for_new_work(project)
    amount = compute_amount([(item.quantity, item.unitPrice) for item in payload.lineItems], payload.discountAmount)

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


def set_status(db: Session, quotation_no: str, new_status: str, reason: str | None, user_id: int) -> Quotation:
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

    audit_service.log_event(
        db, ENTITY_TYPE, quotation.id, "Status changed", user_id,
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


def send_quotation_otp(db: Session, quotation_no: str, user_id: int) -> Quotation:
    """Sends (or resends) the email OTP that gates a quotation into
    "Approved" -- the client-facing counterpart to staff finalizing and
    emailing it (see api/quotations.py's document/email route, unchanged).
    Requires Draft + finalized (the same "content has to be locked
    before a decision is recorded on it" rule set_status already
    enforces) so an OTP is never sent against still-editable content.
    Reuses app/core/otp.py's generation/hashing, shared with client
    onboarding and Requirement confirmation."""
    quotation = get_quotation(db, quotation_no)
    if quotation.status != "Draft" or quotation.finalized_at is None:
        raise ValidationAppError(
            "Save the quotation as Final before sending it to the client for approval."
        )

    code = otp.generate_code()
    quotation.otp_code_hash = otp.hash_code(code)
    quotation.otp_expires_at = otp.new_expiry()
    quotation.otp_attempts = 0
    quotation.otp_sent_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Approval OTP sent", user_id)
    db.commit()
    db.refresh(quotation)

    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    client = db.query(Client).filter(Client.id == project.client_id).first() if project else None
    if client is None:
        raise ValidationAppError("This quotation's project/client record is missing.")

    subject, body = email_template_service.render(
        db,
        "quotation_otp",
        {
            "contact_person": client.contact_person,
            "code": code,
            "quotation_no": quotation.quotation_no,
            "validity_label": otp.validity_label(),
        },
    )
    email_service.send_email(client.email, subject, body, db=db)
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


def verify_quotation_otp(db: Session, quotation_no: str, code: str, user_id: int) -> Quotation:
    """Confirms the code the client read back to staff -- the client's
    acceptance of the quotation. Success is what actually moves the
    quotation to "Approved" (reuses set_status, which already triggers
    project_service.try_auto_advance_stage -- not reimplemented here).

    If the project's scope of work hasn't been reconfirmed by the client
    since it was last edited (project.scope_client_confirmed_at is None
    -- see project_service.save_scope_of_work, which clears it on every
    edit), this same code also serves as that reconfirmation: one OTP
    covers a scope change made mid-negotiation instead of requiring a
    separate round through the Requirement stage's own OTP. Either way,
    the client is emailed a copy of the accepted quotation (PDF
    attached), always with its breakdown and a Payment Plan summary
    when one exists, and with a "what changed in the scope" section
    only when this call also just reconfirmed it.
    """
    quotation = get_quotation(db, quotation_no)
    if quotation.status != "Draft" or quotation.finalized_at is None:
        raise ValidationAppError("This quotation isn't awaiting approval.")
    if not quotation.otp_code_hash or not quotation.otp_expires_at:
        raise ValidationAppError("No verification code has been sent yet. Send one first.")
    if otp.is_expired(quotation.otp_expires_at):
        raise ValidationAppError("This code has expired. Send a new one.")
    if quotation.otp_attempts >= otp.MAX_ATTEMPTS:
        raise ValidationAppError("Too many incorrect attempts. Send a new code.")

    if not otp.code_matches(code, quotation.otp_code_hash):
        quotation.otp_attempts += 1
        db.commit()
        raise ValidationAppError("Incorrect code. Please check with the client and try again.")

    quotation.otp_code_hash = None
    quotation.otp_expires_at = None
    quotation.otp_attempts = 0
    quotation.otp_sent_at = None
    db.commit()

    quotation = set_status(db, quotation_no, "Approved", None, user_id)

    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    scope_was_reconfirmed = project is not None and project.scope_client_confirmed_at is None
    if project is not None and scope_was_reconfirmed:
        project.scope_client_confirmed_at = datetime.now(timezone.utc)
        project.otp_code_hash = None
        project.otp_expires_at = None
        project.otp_attempts = 0
        project.otp_sent_at = None
        audit_service.log_event(
            db, "PROJECT", project.id, "Scope of work confirmed via quotation OTP", user_id
        )
        timeline_service.create_system_event(
            db, project.id, "note", title="Scope of work confirmed by client", description=project.description, actor_id=user_id,
        )
        db.flush()
        project_service.try_auto_advance_stage(db, project, user_id)
        db.commit()
        db.refresh(project)

    if project is None:
        return quotation

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
        )
        db.commit()
    return quotation


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
