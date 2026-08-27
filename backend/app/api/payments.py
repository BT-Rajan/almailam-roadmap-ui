from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.payment import (
    AdjustmentCreate,
    AdjustmentOut,
    FinancialAgreementCreate,
    FinancialAgreementOut,
    FinancialSummaryOut,
    ObligationOut,
    ObligationOverrideUpdate,
    PaymentAllocationOut,
    PaymentOut,
    RecordPaymentInput,
    RefundCreate,
    RefundOut,
)
from app.services import payment_service

router = APIRouter(prefix="/api", tags=["payments"])

can_view = require_permission("Finance", "view")
can_edit = require_permission("Finance", "edit")


def _project_no(db: Session, project_id: int) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.project_no if project else ""


def _user_name(db: Session, user_id: int | None) -> str:
    return payment_service.user_name(db, user_id)


def _agreement_out(db: Session, agreement) -> FinancialAgreementOut:
    return FinancialAgreementOut.from_model(agreement, _project_no(db, agreement.project_id))


def _obligation_out(obligation) -> ObligationOut:
    return ObligationOut.from_model(obligation, obligation.agreement_id)


def _payment_out(db: Session, payment) -> PaymentOut:
    return PaymentOut.from_model(
        payment, payment.agreement_id, _project_no(db, payment.project_id), _user_name(db, payment.created_by)
    )


@router.get("/financial-agreements", response_model=list[FinancialAgreementOut])
def list_agreements(db: Session = Depends(get_db), _=Depends(can_view)):
    return [_agreement_out(db, a) for a in payment_service.list_agreements(db)]


@router.get("/financial-agreements/by-project/{project_no}", response_model=FinancialAgreementOut | None)
def get_agreement_by_project(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    agreement = payment_service.get_agreement_by_project(db, project_no)
    return _agreement_out(db, agreement) if agreement else None


@router.post("/financial-agreements", response_model=FinancialAgreementOut, status_code=201)
def create_agreement(
    payload: FinancialAgreementCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    agreement = payment_service.create_agreement(db, payload, current_user.id)
    return _agreement_out(db, agreement)


@router.get("/financial-agreements/{agreement_id}", response_model=FinancialAgreementOut)
def get_agreement(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    agreement = payment_service.get_agreement(db, payment_service.parse_agreement_id(agreement_id))
    return _agreement_out(db, agreement)


@router.get("/financial-agreements/{agreement_id}/obligations", response_model=list[ObligationOut])
def list_obligations(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    obligations = payment_service.get_obligations(db, payment_service.parse_agreement_id(agreement_id))
    return [_obligation_out(o) for o in obligations]


@router.get("/financial-agreements/{agreement_id}/summary", response_model=FinancialSummaryOut)
def get_summary(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    summary = payment_service.get_financial_summary(db, payment_service.parse_agreement_id(agreement_id))
    next_obligation = summary["nextPaymentObligation"]
    return FinancialSummaryOut(
        contractAmount=float(summary["contractAmount"]),
        estimateAmount=summary["estimateAmount"],
        totalReceived=float(summary["totalReceived"]),
        totalPending=float(summary["totalPending"]),
        totalOverdue=float(summary["totalOverdue"]),
        totalWaived=float(summary["totalWaived"]),
        totalCancelled=float(summary["totalCancelled"]),
        scheduleVariance=float(summary["scheduleVariance"]),
        nextPaymentObligation=_obligation_out(next_obligation) if next_obligation else None,
        nextPaymentDaysUntilDue=summary["nextPaymentDaysUntilDue"],
        nextPaymentIsOverdue=summary["nextPaymentIsOverdue"],
    )


@router.get("/financial-agreements/{agreement_id}/payments", response_model=list[PaymentOut])
def list_payments(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    payments = payment_service.get_payments(db, payment_service.parse_agreement_id(agreement_id))
    return [_payment_out(db, p) for p in payments]


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(
    payload: RecordPaymentInput, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    payment = payment_service.record_payment(db, payload, current_user.id)
    return _payment_out(db, payment)


@router.get("/payments/{payment_id}/allocations", response_model=list[PaymentAllocationOut])
def get_allocations(payment_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    allocations = payment_service.get_allocations_for_payment(db, payment_service.parse_payment_id(payment_id))
    return [
        PaymentAllocationOut(
            id=f"ALC-{a.id:03d}",
            paymentId=f"PMT-{a.payment_id:03d}",
            obligationId=_obligation_display_id(db, a.obligation_id),
            amountAllocated=float(a.amount_allocated),
        )
        for a in allocations
    ]


def _obligation_display_id(db: Session, obligation_id: int) -> str:
    from app.models.payment import PaymentObligation

    obligation = db.query(PaymentObligation).filter(PaymentObligation.id == obligation_id).first()
    return f"OBL-{obligation.agreement_id:03d}-{obligation.sequence_number:02d}" if obligation else ""


@router.get("/obligations", response_model=list[ObligationOut])
def list_all_obligations(db: Session = Depends(get_db), _=Depends(can_view)):
    return [_obligation_out(o) for o in payment_service.list_all_obligations(db)]


@router.patch("/obligations/{obligation_id}/override", response_model=ObligationOut)
def set_obligation_override(
    obligation_id: str,
    payload: ObligationOverrideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    obligation = payment_service.set_obligation_override(
        db, obligation_id, payload.status, payload.reason, current_user.id
    )
    return _obligation_out(obligation)


@router.get("/financial-agreements/{agreement_id}/refunds", response_model=list[RefundOut])
def list_refunds(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    numeric_id = payment_service.parse_agreement_id(agreement_id)
    refunds = payment_service.get_refunds(db, numeric_id)
    return [
        RefundOut(
            id=f"REF-{r.id:03d}",
            paymentId=f"PMT-{r.payment_id:03d}" if r.payment_id else None,
            agreementId=agreement_id,
            refundAmount=float(r.refund_amount),
            refundDate=r.refund_date,
            reason=r.reason,
            authorisingUser=_user_name(db, r.authorising_user),
            reference=r.reference,
        )
        for r in refunds
    ]


@router.post("/financial-agreements/{agreement_id}/refunds", response_model=RefundOut, status_code=201)
def create_refund(
    agreement_id: str,
    payload: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    numeric_id = payment_service.parse_agreement_id(agreement_id)
    refund = payment_service.create_refund(db, payload, current_user.id, numeric_id)
    return RefundOut(
        id=f"REF-{refund.id:03d}",
        paymentId=f"PMT-{refund.payment_id:03d}" if refund.payment_id else None,
        agreementId=agreement_id,
        refundAmount=float(refund.refund_amount),
        refundDate=refund.refund_date,
        reason=refund.reason,
        authorisingUser=current_user.full_name,
        reference=refund.reference,
    )


@router.get("/financial-agreements/{agreement_id}/adjustments", response_model=list[AdjustmentOut])
def list_adjustments(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    numeric_id = payment_service.parse_agreement_id(agreement_id)
    adjustments = payment_service.get_adjustments(db, numeric_id)
    return [
        AdjustmentOut(
            id=f"ADJ-{a.id:03d}",
            agreementId=agreement_id,
            type=a.type,
            amount=float(a.amount),
            reason=a.reason,
            authorisingUser=_user_name(db, a.authorising_user),
            date=a.adjusted_at,
        )
        for a in adjustments
    ]


@router.post("/financial-agreements/{agreement_id}/adjustments", response_model=AdjustmentOut, status_code=201)
def create_adjustment(
    agreement_id: str,
    payload: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    numeric_id = payment_service.parse_agreement_id(agreement_id)
    adjustment = payment_service.create_adjustment(db, payload, current_user.id, numeric_id)
    return AdjustmentOut(
        id=f"ADJ-{adjustment.id:03d}",
        agreementId=agreement_id,
        type=adjustment.type,
        amount=float(adjustment.amount),
        reason=adjustment.reason,
        authorisingUser=current_user.full_name,
        date=adjustment.adjusted_at,
    )


@router.get("/financial-agreements/{agreement_id}/audit-events")
def list_audit_events(agreement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return payment_service.get_audit_events(db, payment_service.parse_agreement_id(agreement_id))
