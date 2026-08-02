from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.quotation import QUOTATION_STATUSES


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class QuotationLineItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: float = Field(gt=0)
    unitPrice: float = Field(ge=0)


class QuotationLineItemOut(BaseModel):
    id: str
    description: str
    quantity: float
    unitPrice: float

    @staticmethod
    def from_model(item) -> "QuotationLineItemOut":
        return QuotationLineItemOut(
            id=f"LI-{item.id:03d}",
            description=item.description,
            quantity=float(item.quantity),
            unitPrice=float(item.unit_price),
        )


class QuotationOut(BaseModel):
    id: str
    projectId: str
    quotationNo: str
    revision: str
    issueDate: date
    validity: date
    status: str
    currency: str
    preparedBy: str
    taxRatePercent: float
    discountAmount: float
    notes: str | None
    termsAndConditions: list[str]
    lineItems: list[QuotationLineItemOut]
    amount: float

    @staticmethod
    def from_model(quotation, project_no: str, prepared_by_name: str, line_items: list) -> "QuotationOut":
        return QuotationOut(
            id=quotation.quotation_no,
            projectId=project_no,
            quotationNo=quotation.quotation_no,
            revision=quotation.revision,
            issueDate=quotation.issue_date,
            validity=quotation.validity,
            status=quotation.status,
            currency=quotation.currency,
            preparedBy=prepared_by_name,
            taxRatePercent=float(quotation.tax_rate_percent),
            discountAmount=float(quotation.discount_amount),
            notes=quotation.notes,
            termsAndConditions=quotation.terms_and_conditions,
            lineItems=[QuotationLineItemOut.from_model(i) for i in line_items],
            amount=float(quotation.amount),
        )


class QuotationCreate(BaseModel):
    projectId: str
    validity: date
    currency: str = Field(default="KWD", min_length=1, max_length=10)
    taxRatePercent: float = Field(default=0, ge=0, le=100)
    discountAmount: float = Field(default=0, ge=0)
    notes: str | None = None
    termsAndConditions: list[str] = Field(default_factory=list)
    lineItems: list[QuotationLineItemIn] = Field(min_length=1)


class QuotationUpdate(BaseModel):
    validity: date | None = None
    taxRatePercent: float | None = Field(default=None, ge=0, le=100)
    discountAmount: float | None = Field(default=None, ge=0)
    notes: str | None = None
    termsAndConditions: list[str] | None = None
    lineItems: list[QuotationLineItemIn] | None = Field(default=None, min_length=1)


class QuotationStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(QUOTATION_STATUSES, "status"))
