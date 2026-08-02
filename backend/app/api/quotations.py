from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.quotation import (
    QuotationCreate,
    QuotationOut,
    QuotationStatusUpdate,
    QuotationUpdate,
)
from app.services import quotation_service

router = APIRouter(prefix="/api/quotations", tags=["quotations"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, quotation) -> QuotationOut:
    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    prepared_by_name = _user_name(db, quotation.prepared_by)
    line_items = quotation_service.get_line_items(db, quotation.id)
    return QuotationOut.from_model(
        quotation, project.project_no if project else "", prepared_by_name, line_items
    )


@router.get("", response_model=list[QuotationOut])
def list_quotations(
    projectId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    return [_to_out(db, q) for q in quotation_service.list_quotations(db, projectId, status)]


@router.get("/{quotation_no}", response_model=QuotationOut)
def get_quotation(quotation_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, quotation_service.get_quotation(db, quotation_no))


@router.post("", response_model=QuotationOut, status_code=201)
def create_quotation(
    payload: QuotationCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    quotation = quotation_service.create_quotation(db, payload, current_user.id)
    return _to_out(db, quotation)


@router.patch("/{quotation_no}", response_model=QuotationOut)
def update_quotation(
    quotation_no: str,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    quotation = quotation_service.update_quotation(db, quotation_no, payload, current_user.id)
    return _to_out(db, quotation)


@router.patch("/{quotation_no}/status", response_model=QuotationOut)
def set_status(
    quotation_no: str,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    quotation = quotation_service.set_status(
        db, quotation_no, payload.status, payload.reason, current_user.id
    )
    return _to_out(db, quotation)


@router.get("/{quotation_no}/audit-events")
def list_audit_events(quotation_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return quotation_service.get_audit_events(db, quotation_no)
