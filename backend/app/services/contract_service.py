from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.status_transitions import (
    CONTRACT_ALLOWED_TRANSITIONS,
    CONTRACT_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.contract import Contract, ContractClause, ContractRevision
from app.models.project import Project
from app.models.user import User
from app.services import audit_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "CONTRACT"


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _next_revision_label(current: str) -> str:
    # Revision labels are 'R0', 'R1', 'R2', ... -- bump the numeric suffix.
    if current.startswith("R") and current[1:].isdigit():
        return f"R{int(current[1:]) + 1}"
    return "R1"


def list_contracts(db: Session, project_no: str | None = None, status: str | None = None) -> list[Contract]:
    query = db.query(Contract).filter(Contract.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(Contract.project_id == (project.id if project else -1))
    if status:
        query = query.filter(Contract.status == status)
    return query.order_by(Contract.id.asc()).all()


def get_contract(db: Session, contract_no: str) -> Contract:
    contract = (
        db.query(Contract).filter(Contract.contract_no == contract_no, Contract.deleted_at.is_(None)).first()
    )
    if contract is None:
        raise NotFoundError("Contract")
    return contract


def get_clauses(db: Session, contract_id: int) -> list[ContractClause]:
    return (
        db.query(ContractClause)
        .filter(ContractClause.contract_id == contract_id)
        .order_by(ContractClause.sort_order.asc(), ContractClause.id.asc())
        .all()
    )


def get_revisions_with_names(db: Session, contract_id: int) -> list[tuple]:
    revisions = (
        db.query(ContractRevision)
        .filter(ContractRevision.contract_id == contract_id)
        .order_by(ContractRevision.id.desc())
        .all()
    )
    return [(r, _user_name(db, r.changed_by)) for r in revisions]


def create_contract(db: Session, payload, user_id: int) -> Contract:
    project = _project_by_no(db, payload.projectId)
    contract = Contract(
        contract_no=next_number(db, "CONTRACT"),
        project_id=project.id,
        template_name=payload.templateName,
        currency=payload.currency,
        contract_value=payload.contractValue,
        issue_date=date.today(),
        expiry_date=payload.expiryDate,
        prepared_by=user_id,
        client_representative=payload.clientRepresentative,
        scope_summary=payload.scopeSummary,
    )
    db.add(contract)
    db.flush()

    for index, clause in enumerate(payload.clauses):
        db.add(
            ContractClause(
                contract_id=contract.id, title=clause.title, content=clause.content, sort_order=index
            )
        )

    audit_service.log_event(db, ENTITY_TYPE, contract.id, "Contract created", user_id, new_value=contract.contract_no)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, contract_no: str, payload, user_id: int) -> Contract:
    contract = get_contract(db, contract_no)
    changes: dict[str, tuple] = {}

    for api_field, attr in (
        ("templateName", "template_name"),
        ("contractValue", "contract_value"),
        ("expiryDate", "expiry_date"),
        ("clientRepresentative", "client_representative"),
        ("scopeSummary", "scope_summary"),
    ):
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(contract, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(contract, attr, value)

    if payload.clauses is not None:
        db.query(ContractClause).filter(ContractClause.contract_id == contract.id).delete()
        for index, clause in enumerate(payload.clauses):
            db.add(
                ContractClause(
                    contract_id=contract.id, title=clause.title, content=clause.content, sort_order=index
                )
            )

    audit_service.log_field_changes(db, ENTITY_TYPE, contract.id, changes, user_id)
    db.commit()
    db.refresh(contract)

    if payload.status is not None and payload.status != contract.status:
        contract = set_status(db, contract_no, payload.status, payload.reason, user_id)

    return contract


def set_status(db: Session, contract_no: str, new_status: str, reason: str | None, user_id: int) -> Contract:
    contract = get_contract(db, contract_no)
    assert_transition_allowed(CONTRACT_ALLOWED_TRANSITIONS, contract.status, new_status, "contract")
    if new_status in CONTRACT_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the contract to '{new_status}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, contract.id, "Status changed", user_id,
        previous_value=contract.status, new_value=new_status, reason=reason,
    )
    contract.status = new_status
    if new_status == "Signed" and contract.signed_date is None:
        contract.signed_date = date.today()

    db.commit()
    db.refresh(contract)
    return contract


def add_revision(db: Session, contract_no: str, summary: str, user_id: int) -> Contract:
    contract = get_contract(db, contract_no)
    new_label = _next_revision_label(contract.revision)
    db.add(
        ContractRevision(
            contract_id=contract.id, revision=new_label, revised_at=date.today(),
            changed_by=user_id, summary=summary,
        )
    )
    audit_service.log_event(
        db, ENTITY_TYPE, contract.id, "Revision recorded", user_id,
        previous_value=contract.revision, new_value=new_label, reason=summary,
    )
    contract.revision = new_label
    db.commit()
    db.refresh(contract)
    return contract


def get_audit_events(db: Session, contract_no: str) -> list[dict]:
    contract = get_contract(db, contract_no)
    return audit_service.get_history(db, ENTITY_TYPE, contract.id)


def delete_contract(db: Session, contract_no: str, actor_id: int) -> None:
    contract = get_contract(db, contract_no)
    audit_service.log_event(db, ENTITY_TYPE, contract.id, "Contract deleted", actor_id, previous_value=contract.contract_no)
    contract.deleted_at = datetime.now(timezone.utc)
    db.commit()
