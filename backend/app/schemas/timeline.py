from datetime import date as date_type

from pydantic import BaseModel, Field


class TimelineEventOut(BaseModel):
    id: str
    projectId: str
    type: str
    title: str
    description: str | None = None
    date: date_type
    status: str
    user: str | None = None

    @staticmethod
    def from_model(event, project_no: str, user_name: str | None) -> "TimelineEventOut":
        return TimelineEventOut(
            id=f"TLE-{event.id:03d}",
            projectId=project_no,
            type=event.type,
            title=event.title,
            description=event.description,
            date=event.event_date,
            status=event.status,
            user=user_name,
        )


class TimelineEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    date: date_type
    status: str = "upcoming"


class TimelineEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    date: date_type | None = None
    status: str | None = None
