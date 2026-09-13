from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.scheduled_report import ScheduledReportIn, ScheduledReportOut
from app.services import scheduled_report_service

router = APIRouter(prefix="/api/scheduled-reports", tags=["scheduled-reports"])

# Same admin surface as every other Administration page (Email Settings,
# Company Settings, ...) -- see require_permission's callers elsewhere.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")
can_delete = require_permission("Administration", "delete")


def _to_out(db: Session, schedule) -> ScheduledReportOut:
    return ScheduledReportOut.from_model(
        schedule,
        scheduled_report_service.project_no_for(db, schedule),
        scheduled_report_service.creator_name(db, schedule),
    )


@router.get("", response_model=list[ScheduledReportOut])
def list_schedules(db: Session = Depends(get_db), _=Depends(can_view)):
    return [_to_out(db, schedule) for schedule in scheduled_report_service.list_schedules(db)]


@router.get("/{schedule_id}", response_model=ScheduledReportOut)
def get_schedule(schedule_id: int, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, scheduled_report_service.get_schedule(db, schedule_id))


@router.post("", response_model=ScheduledReportOut)
def create_schedule(
    payload: ScheduledReportIn, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    schedule = scheduled_report_service.create_schedule(db, payload, current_user.id)
    return _to_out(db, schedule)


@router.patch("/{schedule_id}", response_model=ScheduledReportOut)
def update_schedule(
    schedule_id: int, payload: ScheduledReportIn, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    schedule = scheduled_report_service.update_schedule(db, schedule_id, payload, current_user.id)
    return _to_out(db, schedule)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    scheduled_report_service.delete_schedule(db, schedule_id, current_user.id)


@router.post("/{schedule_id}/send-test", status_code=204)
def send_test_now(schedule_id: int, db: Session = Depends(get_db), _=Depends(can_edit)):
    scheduled_report_service.send_test_now(db, schedule_id)
