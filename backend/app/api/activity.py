import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.activity import ActivityRecordOut, DailySummaryOut, FilterOptionOut
from app.services import activity_service

router = APIRouter(prefix="/api/admin/activity", tags=["activity"])

# Team activity across every project is Administration-level visibility,
# same as the Audit Log it's derived from.
can_view = require_permission("Administration", "view")


@router.get("/day/{day}", response_model=DailySummaryOut)
def get_day_activity(day: str, db: Session = Depends(get_db), _=Depends(can_view)):
    try:
        parsed = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(status_code=422, detail="day must be in YYYY-MM-DD format")
    return activity_service.get_day_activity(db, parsed)


@router.get("/month/{month}", response_model=list[DailySummaryOut])
def get_month_activity(month: str, db: Session = Depends(get_db), _=Depends(can_view)):
    try:
        year_str, month_str = month.split("-")
        year, month_num = int(year_str), int(month_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    return activity_service.get_month_activity(db, year, month_num)


@router.get("/filtered", response_model=list[ActivityRecordOut])
def get_filtered_activities(
    startDate: str,
    endDate: str,
    projectId: str | None = None,
    userId: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    changed_by = int(userId) if userId and userId.isdigit() else None
    return activity_service.get_filtered_activities(db, startDate, endDate, projectId, changed_by, type)


@router.get("/projects", response_model=list[FilterOptionOut])
def get_projects_for_filtering(db: Session = Depends(get_db), _=Depends(can_view)):
    projects = db.query(Project).filter(Project.deleted_at.is_(None)).order_by(Project.project_name.asc()).all()
    return [FilterOptionOut(id=p.project_no, name=p.project_name) for p in projects]


@router.get("/users", response_model=list[FilterOptionOut])
def get_users_for_filtering(db: Session = Depends(get_db), _=Depends(can_view)):
    users = db.query(User).filter(User.deleted_at.is_(None), User.is_active).order_by(User.full_name.asc()).all()
    return [FilterOptionOut(id=str(u.id), name=u.full_name) for u in users]


@router.get("/export/csv")
def export_activities_csv(
    startDate: str,
    endDate: str,
    projectId: str | None = None,
    userId: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    changed_by = int(userId) if userId and userId.isdigit() else None
    activities = activity_service.get_filtered_activities(db, startDate, endDate, projectId, changed_by, type)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Type", "Entity Type", "Entity Name", "Project", "User", "Description", "Timestamp"])
    for activity in activities:
        writer.writerow(
            [
                activity["type"],
                activity["entityType"],
                activity["entityName"],
                activity["projectName"] or "",
                activity["userName"],
                activity["description"],
                activity["timestamp"],
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity-export.csv"},
    )
