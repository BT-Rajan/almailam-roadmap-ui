from datetime import date, datetime, timezone
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
from app.models.user import User
from app.services import audit_service

ENTITY_TYPE = "FINANCIAL_AGREEMENT"


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
    db.commit()
    db.refresh(adjustment)
    return adjustment


def get_adjustments(db: Session, agreement_id: int) -> list[Adjustment]:
    return db.query(Adjustment).filter(Adjustment.agreement_id == agreement_id).order_by(Adjustment.id.desc()).all()


# --- summary and audit ---------------------------------------------------


def get_financial_summary(db: Session, agreement_id: int) -> dict:
    agreement = get_agreement(db, agreement_id)
    obligations = get_obligations(db, agreement_id)
    return calc.get_financial_summary(agreement, obligations)


def get_audit_events(db: Session, agreement_id: int) -> list[dict]:
    get_agreement(db, agreement_id)
    return audit_service.get_history(db, ENTITY_TYPE, agreement_id)
