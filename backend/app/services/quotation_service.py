from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.status_transitions import (
    QUOTATION_ALLOWED_TRANSITIONS,
    QUOTATION_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.project import Project
from app.models.quotation import Quotation, QuotationLineItem
from app.services import audit_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "QUOTATION"


def compute_amount(line_items: list[tuple], tax_rate_percent, discount_amount) -> Decimal:
    """line_items: iterable of (quantity, unit_price) pairs."""
    subtotal = sum(
        (Decimal(str(quantity)) * Decimal(str(unit_price)) for quantity, unit_price in line_items),
        Decimal("0"),
    )
    after_discount = subtotal - Decimal(str(discount_amount))
    return (after_discount * (Decimal("1") + Decimal(str(tax_rate_percent)) / Decimal("100"))).quantize(
        Decimal("0.01")
    )


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


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


def get_line_items(db: Session, quotation_id: int) -> list[QuotationLineItem]:
    return (
        db.query(QuotationLineItem)
        .filter(QuotationLineItem.quotation_id == quotation_id)
        .order_by(QuotationLineItem.id.asc())
        .all()
    )


def create_quotation(db: Session, payload, user_id: int) -> Quotation:
    project = _project_by_no(db, payload.projectId)
    amount = compute_amount(
        [(item.quantity, item.unitPrice) for item in payload.lineItems], payload.taxRatePercent, payload.discountAmount
    )

    quotation = Quotation(
        quotation_no=next_number(db, "QUOTATION"),
        project_id=project.id,
        issue_date=date.today(),
        validity=payload.validity,
        currency=payload.currency,
        prepared_by=user_id,
        tax_rate_percent=payload.taxRatePercent,
        discount_amount=payload.discountAmount,
        notes=payload.notes,
        terms_and_conditions=payload.termsAndConditions,
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
    db.commit()
    db.refresh(quotation)
    return quotation


def update_quotation(db: Session, quotation_no: str, payload, user_id: int) -> Quotation:
    quotation = get_quotation(db, quotation_no)
    changes: dict[str, tuple] = {}

    if payload.validity is not None and payload.validity != quotation.validity:
        changes["validity"] = (quotation.validity, payload.validity)
        quotation.validity = payload.validity
    if payload.notes is not None and payload.notes != quotation.notes:
        changes["notes"] = (quotation.notes, payload.notes)
        quotation.notes = payload.notes
    if payload.termsAndConditions is not None:
        quotation.terms_and_conditions = payload.termsAndConditions

    tax_rate = payload.taxRatePercent if payload.taxRatePercent is not None else quotation.tax_rate_percent
    discount = payload.discountAmount if payload.discountAmount is not None else quotation.discount_amount
    if payload.taxRatePercent is not None:
        changes["tax_rate_percent"] = (quotation.tax_rate_percent, payload.taxRatePercent)
        quotation.tax_rate_percent = payload.taxRatePercent
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

    new_amount = compute_amount(line_items_for_calc, tax_rate, discount)
    if new_amount != quotation.amount:
        changes["amount"] = (quotation.amount, new_amount)
        quotation.amount = new_amount

    audit_service.log_field_changes(db, ENTITY_TYPE, quotation.id, changes, user_id)
    db.commit()
    db.refresh(quotation)
    return quotation


def set_status(db: Session, quotation_no: str, new_status: str, reason: str | None, user_id: int) -> Quotation:
    quotation = get_quotation(db, quotation_no)
    assert_transition_allowed(QUOTATION_ALLOWED_TRANSITIONS, quotation.status, new_status, "quotation")
    if new_status in QUOTATION_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the quotation to '{new_status}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, quotation.id, "Status changed", user_id,
        previous_value=quotation.status, new_value=new_status, reason=reason,
    )
    quotation.status = new_status
    db.commit()
    db.refresh(quotation)
    return quotation


def get_audit_events(db: Session, quotation_no: str) -> list[dict]:
    quotation = get_quotation(db, quotation_no)
    return audit_service.get_history(db, ENTITY_TYPE, quotation.id)


def delete_quotation(db: Session, quotation_no: str, actor_id: int) -> None:
    quotation = get_quotation(db, quotation_no)
    audit_service.log_event(db, ENTITY_TYPE, quotation.id, "Quotation deleted", actor_id, previous_value=quotation.quotation_no)
    quotation.deleted_at = datetime.now(timezone.utc)
    db.commit()
