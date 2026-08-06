import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.audit_log import AuditLogOut
from app.schemas.common import PagedResponse
from app.services import audit_service

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])

can_view = require_permission("Administration", "view")


@router.get("", response_model=PagedResponse[AuditLogOut])
def list_audit_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    changed_by: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    rows, total = audit_service.list_all(
        db, entity_type, entity_id, changed_by, start_date, end_date, page, pageSize
    )
    total_pages = (total + pageSize - 1) // pageSize if pageSize else 0
    return {
        "items": [AuditLogOut.from_row(row) for row in rows],
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "totalPages": total_pages,
    }


@router.get("/export")
def export_audit_logs(
    entity_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    rows, _total = audit_service.list_all(
        db, entity_type=entity_type, start_date=start_date, end_date=end_date, page=1, page_size=5000
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Entity Type", "Entity ID", "Event", "Previous Value", "New Value", "Reason", "Changed By", "Changed At"])
    for row in rows:
        writer.writerow(
            [
                row["entity_type"],
                row["entity_id"],
                row["event_label"],
                row["previous_value"] or "",
                row["new_value"] or "",
                row["reason"] or "",
                row["user"],
                row["changed_at"],
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-log-export.csv"},
    )
