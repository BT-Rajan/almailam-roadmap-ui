from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import payment_calculations as calc
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.status_transitions import (
    OBLIGATION_OVERRIDE_ALLOWED_TRANSITIONS,
    OBLIGATION_OVERRIDE_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.payment import (
    Adjustment,
    FinancialAgreement,
    Payment,
    PaymentAllocation,
    PaymentObligation,
    Refund,
)
from app.models.project import Project
from app.services import notification_service
from app.models.project import Project
from app.models.user import User
from app.services import audit_service

ENTITY_TYPE = "FINANCIAL_AGREEMENT"


def _try_auto_advance_project_stage(db: Session, project_id: int, user_id: int | None) -> None:
    """A payment, refund, or adjustment can be the thing that finally
    settles an agreement -- exactly one of the two conditions
    project_service._assert_stage_exit_criteria requires before
    "Execution & Tracking" can move to "Completed" (the checklist being
    the other). Advance automatically instead of requiring a separate
    manual stage click once both are already true. Local import:
    project_service already imports this module at module level, so
    importing it back at module level here would be circular (see
    audit_service.get_history for the same pattern)."""
    from app.services import project_service

    project = db.query(Project).filter(Project.id == project_id).first()
    if project is not None:
        project_service.try_auto_advance_stage(db, project, user_id)


def parse_agreement_id(raw: str) -> int:
    text = raw.removeprefix("FA-") if raw.upper().startswith("FA-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid agreement id.")
    return int(text)


def parse_obligation_display_id(raw: str) -> tuple[int, int]:
    parts = raw.upper().split("-")
    if len(parts) != 3 or parts[0] != "OBL" or not parts[1].isdigit() or not parts[2].isdigit():
        raise ValidationAppError("Invalid obligation id.")
    return int(parts[1]), int(parts[2])


def parse_payment_id(raw: str) -> int:
    text = raw.removeprefix("PMT-") if raw.upper().startswith("PMT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid payment id.")
    return int(text)


def user_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "System"
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


# --- agreements --------------------------------------------------------


def list_agreements(db: Session) -> list[FinancialAgreement]:
    return db.query(FinancialAgreement).order_by(FinancialAgreement.id.asc()).all()


def get_agreement(db: Session, agreement_id: int) -> FinancialAgreement:
    agreement = db.query(FinancialAgreement).filter(FinancialAgreement.id == agreement_id).first()
    if agreement is None:
        raise NotFoundError("Financial agreement")
    return agreement


def get_agreement_by_project(db: Session, project_no: str) -> FinancialAgreement | None:
    project = db.query(Project).filter(Project.project_no == project_no).first()
    if project is None:
        return None
    return (
        db.query(FinancialAgreement)
        .filter(FinancialAgreement.project_id == project.id)
        .order_by(FinancialAgreement.id.desc())
        .first()
    )


def create_agreement(db: Session, payload, user_id: int) -> FinancialAgreement:
    project = _project_by_no(db, payload.projectId)
    # The staff UI only ever offers "Create Agreement" when none exists
    # yet (hides the button once one does) -- that's a UI convention,
    # not a rule the backend itself enforced, so a race between two
    # requests or a direct API call could previously create a second
    # agreement for the same project with nothing stopping it. The
    # database now also enforces this as a real constraint (see
    # migration 0015), but checking here first means a clear, specific
    # error instead of a raw constraint-violation message.
    existing = get_agreement_by_project(db, payload.projectId)
    if existing:
        raise ValidationAppError(f"{project.project_no} already has a financial agreement -- only one is allowed per project.")
    agreement = FinancialAgreement(
        project_id=project.id,
        contract_amount=payload.contractAmount,
        currency=payload.currency,
        contract_start_date=payload.contractStartDate,
        contract_end_date=payload.contractEndDate,
        agreement_date=payload.agreementDate,
        quotation_reference=payload.quotationReference,
        contract_reference=payload.contractReference,
        payment_mode=payload.paymentMode,
        payment_frequency=payload.paymentFrequency,
    )
    db.add(agreement)
    db.flush()

    schedule = calc.generate_even_schedule(
        Decimal(str(payload.contractAmount)), payload.contractStartDate, payload.contractEndDate,
        payload.paymentFrequency,
    )
    for item in schedule:
        db.add(
            PaymentObligation(
                agreement_id=agreement.id,
                sequence_number=item["sequenceNumber"],
                description=item["description"],
                amount_due=item["amountDue"],
                due_date=item["dueDate"],
                amount_received=0,
            )
        )

    audit_service.log_event(db, ENTITY_TYPE, agreement.id, "Agreement Created", user_id)
    for _ in schedule:
        audit_service.log_event(db, ENTITY_TYPE, agreement.id, "Obligation Created", user_id)

    db.commit()
    db.refresh(agreement)
    return agreement


# --- obligations -----------------------------------------------------------


def get_obligations(db: Session, agreement_id: int) -> list[PaymentObligation]:
    return (
        db.query(PaymentObligation)
        .filter(PaymentObligation.agreement_id == agreement_id)
        .order_by(PaymentObligation.sequence_number.asc())
        .all()
    )


def list_all_obligations(db: Session) -> list[PaymentObligation]:
    return (
        db.query(PaymentObligation)
        .order_by(PaymentObligation.agreement_id.asc(), PaymentObligation.sequence_number.asc())
        .all()
    )


def get_obligation_by_display_id(db: Session, raw_id: str) -> PaymentObligation:
    """Locks the row (SELECT ... FOR UPDATE) for the remainder of the
    caller's transaction. Every call site mutates amount_received/
    amount_due and commits right after -- without this, two concurrent
    requests touching the same obligation (two payments, or a payment
    racing a refund/adjustment) can each read the same starting balance
    and one write silently clobbers the other on commit. Mirrors the
    same pattern already used correctly in number_series_service.py."""
    agreement_id, sequence_number = parse_obligation_display_id(raw_id)
    obligation = (
        db.query(PaymentObligation)
        .filter(
            PaymentObligation.agreement_id == agreement_id,
            PaymentObligation.sequence_number == sequence_number,
        )
        .with_for_update()
        .first()
    )
    if obligation is None:
        raise NotFoundError("Payment obligation")
    return obligation


def set_obligation_override(db: Session, raw_id: str, new_status: str, reason: str | None, user_id: int) -> PaymentObligation:
    obligation = get_obligation_by_display_id(db, raw_id)
    current = obligation.manual_status or "Computed"
    assert_transition_allowed(OBLIGATION_OVERRIDE_ALLOWED_TRANSITIONS, current, new_status, "payment obligation")
    if new_status in OBLIGATION_OVERRIDE_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move this obligation to '{new_status}'.")

    event_label = {
        "Cancelled": "Obligation Cancelled",
        "Waived": "Obligation Waived",
        "Computed": "Obligation Override Cleared",
    }[new_status]
    audit_service.log_event(
        db, ENTITY_TYPE, obligation.agreement_id, event_label, user_id,
        new_value=obligation.description, reason=reason,
    )
    obligation.manual_status = None if new_status == "Computed" else new_status
    db.commit()
    db.refresh(obligation)
    return obligation


# --- payments and allocations ------------------------------------------


def get_payments(db: Session, agreement_id: int) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.agreement_id == agreement_id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
        .all()
    )


def get_allocations_for_payment(db: Session, payment_id: int) -> list[PaymentAllocation]:
    return db.query(PaymentAllocation).filter(PaymentAllocation.payment_id == payment_id).all()


def record_payment(db: Session, payload, user_id: int) -> Payment:
    agreement = get_agreement(db, parse_agreement_id(payload.agreementId))

    allocation_targets: list[tuple[PaymentObligation, float]] = []
    total_allocated = Decimal("0")
    # Sorted by obligationId (not payload order) before locking any of
    # them: a payment can touch several obligations at once, and if two
    # concurrent payments lock the same set in different orders, MySQL
    # can deadlock instead of one just waiting for the other. A fixed,
    # consistent lock-acquisition order avoids that.
    for allocation_input in sorted(payload.allocations, key=lambda a: a.obligationId):
        obligation = get_obligation_by_display_id(db, allocation_input.obligationId)
        if obligation.agreement_id != agreement.id:
            raise ValidationAppError("An allocation targets an obligation from a different agreement.")
        allocation_targets.append((obligation, allocation_input.amount))
        total_allocated += Decimal(str(allocation_input.amount))

    if total_allocated > Decimal(str(payload.amountReceived)):
        raise ValidationAppError("Total allocated amount cannot exceed the amount received.")

    payment = Payment(
        agreement_id=agreement.id,
        project_id=agreement.project_id,
        amount_received=payload.amountReceived,
        payment_date=payload.paymentDate,
        payment_mode=payload.paymentMode,
        reference_number=payload.referenceNumber,
        payer=payload.payer,
        receiving_account=payload.receivingAccount,
        notes=payload.notes,
        created_by=user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    db.flush()

    for obligation, amount in allocation_targets:
        remaining = Decimal(str(obligation.amount_due)) - Decimal(str(obligation.amount_received))
        if Decimal(str(amount)) > remaining:
            raise ValidationAppError(
                f"Allocation of {amount} to '{obligation.description}' exceeds the {remaining} still outstanding on it."
            )
        db.add(PaymentAllocation(payment_id=payment.id, obligation_id=obligation.id, amount_allocated=amount))
        was_settled = obligation.amount_received >= obligation.amount_due
        obligation.amount_received = float(Decimal(str(obligation.amount_received)) + Decimal(str(amount)))
        if not was_settled and obligation.amount_received >= obligation.amount_due:
            obligation.date_paid = payload.paymentDate
            obligation.payment_method = payload.paymentMode
            obligation.reference_number = payload.referenceNumber

    mode_label = "payment" if payload.paymentMode == "Other" else f"{payload.amountReceived} via {payload.paymentMode}"
    audit_service.log_event(db, ENTITY_TYPE, agreement.id, "Payment Received", user_id, new_value=mode_label)
    if allocation_targets:
        allocation_summary = ", ".join(
            f"{amount} -> OBL-{agreement.id:03d}-{obligation.sequence_number:02d}"
            for obligation, amount in allocation_targets
        )
        audit_service.log_event(
            db, ENTITY_TYPE, agreement.id, "Payment Allocated", user_id, new_value=allocation_summary
        )

    _try_auto_advance_project_stage(db, agreement.project_id, user_id)
    db.commit()
    db.refresh(payment)
    return payment


# --- refunds -----------------------------------------------------------


def create_refund(db: Session, payload, user_id: int, agreement_id: int) -> Refund:
    obligation = get_obligation_by_display_id(db, payload.obligationId)
    if obligation.agreement_id != agreement_id:
        raise ValidationAppError("obligationId does not belong to this agreement.")
    if Decimal(str(payload.refundAmount)) > Decimal(str(obligation.amount_received)):
        raise ValidationAppError("Refund amount cannot exceed the amount already received for this obligation.")

    related_allocation = (
        db.query(PaymentAllocation).filter(PaymentAllocation.obligation_id == obligation.id).first()
    )
    refund = Refund(
        payment_id=related_allocation.payment_id if related_allocation else None,
        agreement_id=agreement_id,
        obligation_id=obligation.id,
        refund_amount=payload.refundAmount,
        refund_date=payload.refundDate,
        reason=payload.reason,
        authorising_user=user_id,
        reference=payload.reference,
    )
    db.add(refund)

    obligation.amount_received = max(
        0.0, float(Decimal(str(obligation.amount_received)) - Decimal(str(payload.refundAmount)))
    )

    audit_service.log_event(
        db, ENTITY_TYPE, agreement_id, "Payment Refunded", user_id,
        new_value=f"{payload.refundAmount} refunded against OBL-{agreement_id:03d}-{obligation.sequence_number:02d}",
        reason=payload.reason,
    )
    # No auto-advance here, unlike record_payment/create_adjustment below --
    # a refund only ever reduces amount_received, so it can never newly
    # satisfy the "payment settled" exit criterion, only make it harder to
    # reach.
    db.commit()
    db.refresh(refund)
    return refund


def get_refunds(db: Session, agreement_id: int) -> list[Refund]:
    return db.query(Refund).filter(Refund.agreement_id == agreement_id).order_by(Refund.id.desc()).all()


# --- adjustments ----------------------------------------------------------


def create_adjustment(db: Session, payload, user_id: int, agreement_id: int) -> Adjustment:
    obligation = get_obligation_by_display_id(db, payload.obligationId)
    if obligation.agreement_id != agreement_id:
        raise ValidationAppError("obligationId does not belong to this agreement.")

    adjustment = Adjustment(
        agreement_id=agreement_id,
        obligation_id=obligation.id,
        type=payload.type,
        amount=payload.amount,
        reason=payload.reason,
        authorising_user=user_id,
        adjusted_at=date.today(),
    )
    db.add(adjustment)

    previous_value = f"{obligation.description}: {obligation.amount_due}"
    delta = -Decimal(str(payload.amount)) if payload.type == "Decrease" else Decimal(str(payload.amount))
    obligation.amount_due = max(0.0, float(Decimal(str(obligation.amount_due)) + delta))

    audit_service.log_event(
        db, ENTITY_TYPE, agreement_id, "Adjustment Applied", user_id,
        previous_value=previous_value, new_value=f"{obligation.description}: {obligation.amount_due}",
        reason=payload.reason,
    )
    # A Decrease can be exactly what brings an agreement to fully paid --
    # harmless to check regardless of adjustment type, since
    # try_auto_advance_stage no-ops if the exit criteria aren't met.
    _try_auto_advance_project_stage(db, get_agreement(db, agreement_id).project_id, user_id)
    db.commit()
    db.refresh(adjustment)
    return adjustment


def get_adjustments(db: Session, agreement_id: int) -> list[Adjustment]:
    return db.query(Adjustment).filter(Adjustment.agreement_id == agreement_id).order_by(Adjustment.id.desc()).all()


# --- summary and audit ---------------------------------------------------


def get_financial_summary(db: Session, agreement_id: int) -> dict:
    agreement = get_agreement(db, agreement_id)
    obligations = get_obligations(db, agreement_id)
    payments = get_payments(db, agreement_id)
    refunds = get_refunds(db, agreement_id)
    return calc.get_financial_summary(agreement, obligations, payments, refunds)


def get_audit_events(db: Session, agreement_id: int) -> list[dict]:
    get_agreement(db, agreement_id)
    return audit_service.get_history(db, ENTITY_TYPE, agreement_id)


# (due_date offset in days, the column that guards against re-sending,
# title, and the message-tense to use) -- one entry per reminder point.
_REMINDER_POINTS = (
    (-2, "reminder_before_sent_at", "Payment due in 2 days", "is due in 2 days, on"),
    (0, "reminder_due_sent_at", "Payment due today", "is due today,"),
    (2, "reminder_after_sent_at", "Payment overdue", "was due 2 days ago, on"),
)


def check_and_notify_payment_reminders(db: Session, today: date | None = None) -> int:
    """Finds payment obligations due_date +/- 2 days from today and not
    yet settled, and notifies the project's engineer once per reminder
    point (2 days before, on the day, 2 days after) -- the
    reminder_*_sent_at columns are the same once-per-episode idempotency
    guard as Project.stale_notified_at, just three of them since there
    are three distinct points instead of one ongoing state.

    Stops entirely, permanently, the moment date_paid is set -- "payment
    confirmation has arrived" -- rather than tracking a separate
    cancellation flag; Cancelled/Waived obligations are excluded the same
    way active_obligations excludes them in get_financial_summary, since
    neither represents money still expected to arrive.

    Called periodically by the background scheduler (see main.py's
    lifespan), but is itself a plain, directly-callable function --
    deliberately not scheduling logic of its own, so the actual
    due-date arithmetic can be tested without waiting on a real clock.
    `today` is only ever overridden by tests; production calls always
    let it default.

    Returns how many reminders were newly sent in this run.
    """
    today = today or datetime.now(timezone.utc).date()

    candidates = (
        db.query(PaymentObligation)
        .filter(PaymentObligation.date_paid.is_(None), PaymentObligation.manual_status.is_(None))
        .all()
    )

    notified_count = 0
    for obligation in candidates:
        for offset_days, guard_column, title, tense in _REMINDER_POINTS:
            if obligation.due_date != today - timedelta(days=offset_days):
                continue
            if getattr(obligation, guard_column) is not None:
                continue

            agreement = get_agreement(db, obligation.agreement_id)
            project = db.query(Project).filter(Project.id == agreement.project_id).first()
            if project is None or project.engineer_id is None:
                continue

            notification_service.create_notification(
                db, project.engineer_id,
                title,
                f"Payment of {obligation.amount_due} {agreement.currency} for {project.project_name} "
                f"({project.project_no}) {tense} {obligation.due_date.isoformat()}.",
                "Payment",
                link_route_name="payments",
            )
            setattr(obligation, guard_column, datetime.now(timezone.utc))
            notified_count += 1

    db.commit()
    return notified_count
