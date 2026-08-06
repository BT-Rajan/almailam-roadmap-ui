from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    entityType: str
    entityId: str
    eventLabel: str
    previousValue: str | None = None
    newValue: str | None = None
    reason: str | None = None
    changedBy: str
    changedAt: datetime

    @staticmethod
    def from_row(row: dict) -> "AuditLogOut":
        return AuditLogOut(
            id=str(row["id"]),
            entityType=row["entity_type"],
            entityId=str(row["entity_id"]),
            eventLabel=row["event_label"],
            previousValue=row["previous_value"],
            newValue=row["new_value"],
            reason=row["reason"],
            changedBy=row["user"],
            changedAt=row["changed_at"],
        )
