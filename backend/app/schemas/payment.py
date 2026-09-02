from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core import payment_calculations as calc
from app.models.payment import ADJUSTMENT_TYPES, PAYMENT_FREQUENCIES, PAYMENT_MODES

MAX_MILESTONES = 5


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


def _optional_enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str | None) -> str | None:
        if value is not None and value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


# --- financial agreement -------------------------------------------------


class FinancialAgreementOut(BaseModel):
    id: str
    projectId: str
    stream: Literal["Design", "Supervision"]
    # See AGREEMENT_STATUSES -- gates the Payment Plan -> Contract stage
    # transition (project_service._assert_stage_exit_criteria).
    status: Literal["Draft", "Approved"]
    contractAmount: float
    currency: str
    contractStartDate: date
    contractEndDate: date | None
    agreementDate: date
    quotationReference: str | None
    contractReference: str | None
    paymentMode: str
    paymentFrequency: str

    @staticmethod
    def from_model(agreement, project_no: str) -> "FinancialAgreementOut":
        return FinancialAgreementOut(
            id=f"FA-{agreement.id:03d}",
            projectId=project_no,
            stream=agreement.stream,
            status=agreement.status,
            contractAmount=float(agreement.contract_amount),
            currency=agreement.currency,
            contractStartDate=agreement.contract_start_date,
            contractEndDate=agreement.contract_end_date,
            agreementDate=agreement.agreement_date,
            quotationReference=agreement.quotation_reference,
            contractReference=agreement.contract_reference,
            paymentMode=agreement.payment_mode,
            paymentFrequency=agreement.payment_frequency,
        )


class MilestoneInput(BaseModel):
    """One row of a milestone payment plan (e.g. '25% at signup') --
    percentage is of the agreement's contractAmount, not a fixed sum, so
    the plan still makes sense if contractAmount is edited before submit."""

    description: str = Field(min_length=1, max_length=100)
    percentage: float = Field(gt=0, le=100)
    dueDate: date


class FinancialAgreementCreate(BaseModel):
    projectId: str
    # Design (the default, matching every agreement created before this
    # field existed) keeps today's exact behavior: contractAmount/
    # contractStartDate/paymentFrequency are required and drive
    # generate_even_schedule. Supervision instead derives all of these
    # server-side from the project's selected Supervision activities via
    # generate_prorated_monthly_schedule -- see payment_service.
    # create_agreement -- so they're optional here rather than required.
    stream: Literal["Design", "Supervision"] = "Design"
    contractAmount: float | None = Field(default=None, gt=0)
    currency: str = Field(default="KWD", min_length=1, max_length=10)
    contractStartDate: date | None = None
    contractEndDate: date | None = None
    agreementDate: date
    quotationReference: str | None = Field(default=None, max_length=30)
    contractReference: str | None = Field(default=None, max_length=30)
    paymentMode: str
    paymentFrequency: str | None = None
    # A milestone plan (e.g. 25% at signup / 25% on design approval /
    # 25% on approval filed / final on handover) -- an alternative to
    # paymentFrequency's date-interval split, used when paymentFrequency
    # is "Custom". Ignored for Supervision, which always derives its own
    # (monthly, prorated) schedule server-side.
    milestones: list[MilestoneInput] | None = None

    _check_mode = field_validator("paymentMode")(_enum_validator(PAYMENT_MODES, "paymentMode"))
    _check_freq = field_validator("paymentFrequency")(_optional_enum_validator(PAYMENT_FREQUENCIES, "paymentFrequency"))

    @model_validator(mode="after")
    def _check_milestones(self) -> "FinancialAgreementCreate":
        if self.milestones is None:
            return self
        if len(self.milestones) > MAX_MILESTONES:
            raise ValueError(f"A payment plan can have at most {MAX_MILESTONES} installments.")
        total = sum((Decimal(str(m.percentage)) for m in self.milestones), Decimal("0"))
        # Allow a hair of rounding slack (e.g. three 33.33% rows) but
        # not a plan that's actually short of or over 100%.
        if abs(total - Decimal("100")) > Decimal("0.5"):
            raise ValueError(f"Milestone percentages must add up to 100% (currently {total}%).")
        return self


# --- obligation ------------------------------------------------------------


class ObligationOut(BaseModel):
    id: str
    agreementId: str
    sequenceNumber: int
    description: str
    amountDue: float
    dueDate: date
    amountReceived: float
    status: str
    manualStatus: str | None
    datePaid: date | None
    paymentMethod: str | None
    referenceNumber: str | None
    notes: str | None

    @staticmethod
    def from_model(obligation, agreement_display_no: int) -> "ObligationOut":
        return ObligationOut(
            id=f"OBL-{agreement_display_no:03d}-{obligation.sequence_number:02d}",
            agreementId=f"FA-{agreement_display_no:03d}",
            sequenceNumber=obligation.sequence_number,
            description=obligation.description,
            amountDue=float(obligation.amount_due),
            dueDate=obligation.due_date,
            amountReceived=float(obligation.amount_received),
            status=calc.compute_obligation_status(obligation),
            manualStatus=obligation.manual_status,
            datePaid=obligation.date_paid,
            paymentMethod=obligation.payment_method,
            referenceNumber=obligation.reference_number,
            notes=obligation.notes,
        )


class ObligationOverrideUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(("Computed", "Cancelled", "Waived"), "status"))


# --- payment + allocations -----------------------------------------------


class PaymentAllocationInput(BaseModel):
    obligationId: str
    amount: float = Field(gt=0)


class PaymentAllocationOut(BaseModel):
    id: str
    paymentId: str
    obligationId: str
    amountAllocated: float


class PaymentOut(BaseModel):
    id: str
    agreementId: str
    projectId: str
    amountReceived: float
    paymentDate: date
    paymentMode: str
    referenceNumber: str | None
    payer: str
    receivingAccount: str | None
    notes: str | None
    createdBy: str
    createdDate: datetime

    @staticmethod
    def from_model(payment, agreement_display_no: int, project_no: str, created_by_name: str) -> "PaymentOut":
        return PaymentOut(
            id=f"PMT-{payment.id:03d}",
            agreementId=f"FA-{agreement_display_no:03d}",
            projectId=project_no,
            amountReceived=float(payment.amount_received),
            paymentDate=payment.payment_date,
            paymentMode=payment.payment_mode,
            referenceNumber=payment.reference_number,
            payer=payment.payer,
            receivingAccount=payment.receiving_account,
            notes=payment.notes,
            createdBy=created_by_name,
            createdDate=payment.created_at,
        )


class RecordPaymentInput(BaseModel):
    agreementId: str
    amountReceived: float = Field(gt=0)
    paymentDate: date
    paymentMode: str
    referenceNumber: str | None = Field(default=None, max_length=60)
    payer: str = Field(min_length=1, max_length=150)
    receivingAccount: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    allocations: list[PaymentAllocationInput] = Field(default_factory=list)

    _check_mode = field_validator("paymentMode")(_enum_validator(PAYMENT_MODES, "paymentMode"))


# --- refunds and adjustments -----------------------------------------------


class RefundOut(BaseModel):
    id: str
    paymentId: str | None
    agreementId: str
    refundAmount: float
    refundDate: date
    reason: str
    authorisingUser: str
    reference: str | None


class RefundCreate(BaseModel):
    obligationId: str
    refundAmount: float = Field(gt=0)
    refundDate: date
    reason: str = Field(min_length=1)
    reference: str | None = Field(default=None, max_length=60)


class AdjustmentOut(BaseModel):
    id: str
    agreementId: str
    type: str
    amount: float
    reason: str
    authorisingUser: str
    date: date


class AdjustmentCreate(BaseModel):
    obligationId: str
    type: str
    amount: float = Field(gt=0)
    reason: str = Field(min_length=1)
    _check_type = field_validator("type")(_enum_validator(ADJUSTMENT_TYPES, "type"))


# --- summary ---------------------------------------------------------------


class FinancialSummaryOut(BaseModel):
    contractAmount: float
    # The originating quotation's amount, if the agreement was created
    # from one (see payment_service.get_financial_summary) -- None when
    # there's no linked quotation to look up.
    estimateAmount: float | None = None
    totalReceived: float
    totalPending: float
    totalOverdue: float
    totalWaived: float
    totalCancelled: float
    scheduleVariance: float
    nextPaymentObligation: ObligationOut | None
    nextPaymentDaysUntilDue: int | None
    nextPaymentIsOverdue: bool
