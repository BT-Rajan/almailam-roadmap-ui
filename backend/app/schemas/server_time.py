from pydantic import BaseModel


class ServerTimeOut(BaseModel):
    # ISO date (YYYY-MM-DD) and full ISO 8601 datetime with the +03:00
    # offset explicit -- both always Kuwait local time (see
    # app.core.kuwait_time), never the server's own configured
    # timezone. The frontend uses this as the sole source of "today"
    # for every overdue/due-date/expiry decision instead of the
    # visiting browser's own clock -- see src/utils/serverTime.ts.
    date: str
    datetime: str
    timezone: str
