from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.ai_review import ContractAISummaryOut
from app.schemas.contract import (
    ContractCreate,
    ContractOut,
    ContractRevisionCreate,
    ContractStatusUpdate,
    ContractUpdate,
)
from app.services import contract_service

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, contract) -> ContractOut:
    from app.models.quotation import Quotation

    project = db.query(Project).filter(Project.id == contract.project_id).first()
    prepared_by_name = _user_name(db, contract.prepared_by)
    clauses = contract_service.get_clauses(db, contract.id)
    revisions = contract_service.get_revisions_with_names(db, contract.id)
    quotation_no = None
    if contract.quotation_id is not None:
        quotation = db.query(Quotation).filter(Quotation.id == contract.quotation_id).first()
        quotation_no = quotation.quotation_no if quotation else None
    return ContractOut.from_model(
        contract, project.project_no if project else "", prepared_by_name, clauses, revisions, quotation_no
    )


@router.get("", response_model=list[ContractOut])
def list_contracts(
    projectId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    return [_to_out(db, c) for c in contract_service.list_contracts(db, projectId, status)]


@router.get("/{contract_no}", response_model=ContractOut)
def get_contract(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, contract_service.get_contract(db, contract_no))


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(
    payload: ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    contract = contract_service.create_contract(db, payload, current_user.id)
    return _to_out(db, contract)


@router.patch("/{contract_no}", response_model=ContractOut)
def update_contract(
    contract_no: str,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.update_contract(db, contract_no, payload, current_user.id)
    return _to_out(db, contract)


@router.post("/{contract_no}/finalize", response_model=ContractOut)
def finalize_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    contract = contract_service.finalize_contract(db, contract_no, current_user.id)
    return _to_out(db, contract)


@router.post("/{contract_no}/reopen", response_model=ContractOut)
def reopen_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    contract = contract_service.reopen_contract(db, contract_no, current_user.id)
    return _to_out(db, contract)


@router.patch("/{contract_no}/status", response_model=ContractOut)
def set_status(
    contract_no: str,
    payload: ContractStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.set_status(
        db, contract_no, payload.status, payload.reason, current_user.id
    )
    return _to_out(db, contract)


@router.post("/{contract_no}/revisions", response_model=ContractOut, status_code=201)
def add_revision(
    contract_no: str,
    payload: ContractRevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.add_revision(db, contract_no, payload.summary, current_user.id)
    return _to_out(db, contract)


@router.get("/{contract_no}/audit-events")
def list_audit_events(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return contract_service.get_audit_events(db, contract_no)


@router.delete("/{contract_no}", status_code=204)
def delete_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    contract_service.delete_contract(db, contract_no, current_user.id)


@router.get("/{contract_no}/ai-summary", response_model=ContractAISummaryOut)
async def get_contract_ai_summary(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    from app.models.project import Project
    from app.services import ai_service

    contract = contract_service.get_contract(db, contract_no)
    clauses = contract_service.get_clauses(db, contract.id)
    project = db.query(Project).filter(Project.id == contract.project_id).first()
    try:
        return await ai_service.get_contract_summary(db, contract, clauses, project)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
