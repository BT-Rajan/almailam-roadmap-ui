from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.contract import CONTRACT_STATUSES


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
            finalizedAt=contract.finalized_at,
        )


class ContractCreate(BaseModel):
    projectId: str
    quotationId: str = Field(min_length=1)
    currency: str = Field(default="KWD", min_length=1, max_length=10)
    contractValue: float = Field(gt=0)
    expiryDate: date
    clientRepresentative: str = Field(min_length=1, max_length=150)
    scopeSummary: str = Field(min_length=1)
    clauses: list[ContractClauseIn] = Field(default_factory=list)


class ContractUpdate(BaseModel):
    contractValue: float | None = Field(default=None, gt=0)
    expiryDate: date | None = None
    clientRepresentative: str | None = Field(default=None, min_length=1, max_length=150)
    scopeSummary: str | None = None
    clauses: list[ContractClauseIn] | None = None
    status: str | None = None
    reason: str | None = None

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTRACT_STATUSES:
            raise ValueError(f"status must be one of {CONTRACT_STATUSES}")
        return value


class ContractStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(CONTRACT_STATUSES, "status"))
