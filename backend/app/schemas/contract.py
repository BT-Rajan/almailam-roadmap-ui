from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.contract import CONTRACT_FEE_FREQUENCIES, CONTRACT_STATUSES, CONTRACT_TEMPLATE_KEYS


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class ContractClauseIn(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    content: str = Field(min_length=1)


class ContractClauseOut(BaseModel):
    id: str
    title: str
    content: str

    @staticmethod
    def from_model(clause) -> "ContractClauseOut":
        return ContractClauseOut(id=f"CL-{clause.id:03d}", title=clause.title, content=clause.content)


class ContractRevisionOut(BaseModel):
    id: str
    revision: str
    date: date
    changedBy: str
    summary: str

    @staticmethod
    def from_model(revision, changed_by_name: str) -> "ContractRevisionOut":
        return ContractRevisionOut(
            id=f"REV-{revision.id:03d}",
            revision=revision.revision,
            date=revision.revised_at,
            changedBy=changed_by_name,
            summary=revision.summary,
        )


class ContractRevisionCreate(BaseModel):
    summary: str = Field(min_length=1)


class ContractOut(BaseModel):
    id: str
    projectId: str
    quotationNo: str | None
    contractNo: str
    templateName: str
    revision: str
    currency: str
    contractValue: float
    issueDate: date
    signedDate: date | None
    expiryDate: date
    status: str
    preparedBy: str
    clientRepresentative: str
    scopeSummary: str
    clauses: list[ContractClauseOut]
    revisions: list[ContractRevisionOut]
    templateKey: str | None
    isBilingual: bool
    subjectLineAr: str | None
    subjectLineEn: str | None
    projectReference: str | None
    feeFrequency: str
    scopeItemsAr: list[str]
    scopeItemsEn: list[str]
    paymentTermsAr: list[str]
    paymentTermsEn: list[str]
    finalizedAt: datetime | None

    @staticmethod
    def from_model(
        contract, project_no: str, prepared_by_name: str, clauses: list, revisions: list[tuple],
        quotation_no: str | None = None,
    ) -> "ContractOut":
        return ContractOut(
            id=contract.contract_no,
            projectId=project_no,
            quotationNo=quotation_no,
            contractNo=contract.contract_no,
            templateName=contract.template_name,
            revision=contract.revision,
            currency=contract.currency,
            contractValue=float(contract.contract_value),
            issueDate=contract.issue_date,
            signedDate=contract.signed_date,
            expiryDate=contract.expiry_date,
            status=contract.status,
            preparedBy=prepared_by_name,
            clientRepresentative=contract.client_representative,
            scopeSummary=contract.scope_summary,
            clauses=[ContractClauseOut.from_model(c) for c in clauses],
            revisions=[ContractRevisionOut.from_model(r, name) for r, name in revisions],
            templateKey=contract.template_key,
            isBilingual=contract.is_bilingual,
            subjectLineAr=contract.subject_line_ar,
            subjectLineEn=contract.subject_line_en,
            projectReference=contract.project_reference,
            feeFrequency=contract.fee_frequency,
            scopeItemsAr=contract.scope_items_ar,
            scopeItemsEn=contract.scope_items_en,
            paymentTermsAr=contract.payment_terms_ar,
            paymentTermsEn=contract.payment_terms_en,
            finalizedAt=contract.finalized_at,
        )


class ContractCreate(BaseModel):
    projectId: str
    quotationId: str = Field(min_length=1)
    templateName: str = Field(min_length=1, max_length=150)
    currency: str = Field(default="KWD", min_length=1, max_length=10)
    contractValue: float = Field(gt=0)
    expiryDate: date
    clientRepresentative: str = Field(min_length=1, max_length=150)
    scopeSummary: str = Field(min_length=1)
    clauses: list[ContractClauseIn] = Field(default_factory=list)
    # Lettered-template fields -- all optional; a contract created
    # without templateKey renders in the original generic clause layout.
    templateKey: str | None = None
    isBilingual: bool = False
    subjectLineAr: str | None = Field(default=None, max_length=300)
    subjectLineEn: str | None = Field(default=None, max_length=300)
    projectReference: str | None = Field(default=None, max_length=300)
    feeFrequency: str = Field(default="Lump Sum")
    scopeItemsAr: list[str] = Field(default_factory=list)
    scopeItemsEn: list[str] = Field(default_factory=list)
    paymentTermsAr: list[str] = Field(default_factory=list)
    paymentTermsEn: list[str] = Field(default_factory=list)

    @field_validator("templateKey")
    @classmethod
    def check_template_key(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTRACT_TEMPLATE_KEYS:
            raise ValueError(f"templateKey must be one of {CONTRACT_TEMPLATE_KEYS}")
        return value

    @field_validator("feeFrequency")
    @classmethod
    def check_fee_frequency(cls, value: str) -> str:
        if value not in CONTRACT_FEE_FREQUENCIES:
            raise ValueError(f"feeFrequency must be one of {CONTRACT_FEE_FREQUENCIES}")
        return value


class ContractUpdate(BaseModel):
    templateName: str | None = Field(default=None, min_length=1, max_length=150)
    contractValue: float | None = Field(default=None, gt=0)
    expiryDate: date | None = None
    clientRepresentative: str | None = Field(default=None, min_length=1, max_length=150)
    scopeSummary: str | None = None
    clauses: list[ContractClauseIn] | None = None
    status: str | None = None
    reason: str | None = None
    subjectLineAr: str | None = Field(default=None, max_length=300)
    subjectLineEn: str | None = Field(default=None, max_length=300)
    projectReference: str | None = Field(default=None, max_length=300)
    feeFrequency: str | None = None
    scopeItemsAr: list[str] | None = None
    scopeItemsEn: list[str] | None = None
    paymentTermsAr: list[str] | None = None
    paymentTermsEn: list[str] | None = None

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTRACT_STATUSES:
            raise ValueError(f"status must be one of {CONTRACT_STATUSES}")
        return value

    @field_validator("feeFrequency")
    @classmethod
    def check_fee_frequency(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTRACT_FEE_FREQUENCIES:
            raise ValueError(f"feeFrequency must be one of {CONTRACT_FEE_FREQUENCIES}")
        return value


class ContractStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(CONTRACT_STATUSES, "status"))
