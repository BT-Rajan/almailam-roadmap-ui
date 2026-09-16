"""Kuwait-local "today"/"now" for date-sensitive business decisions --
payment obligation overdue status, quotation/contract expiry, report
period boundaries, and every timestamp recorded against an action a
Kuwait-based user just took.

This app's servers commonly run on UTC (or whatever timezone the host
happens to be configured with), and browsers report whatever timezone
the visitor's device is set to -- neither is guaranteed to be Kuwait
time (UTC+3, no DST). A visitor or server in a different zone can
disagree with Kuwait about what "today" is for several hours around
each UTC midnight, which is exactly the window where "is this payment
overdue yet" or "has this contract expired yet" needs to be right.

Originally a private helper in status_report_service.py (for the "only
today's report is editable, until 11:59 PM Kuwait time" rule) --
pulled out here so every other date-sensitive decision in the app uses
the same convention instead of each service re-deriving its own notion
of "today" from the server's local clock.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

KUWAIT_TIMEZONE = "Asia/Kuwait"


def kuwait_now() -> datetime:
    """Falls back to naive server-local time if the "Asia/Kuwait" zone
    can't be loaded (e.g. no tzdata installed) rather than raising in
    the middle of an unrelated action -- a wrong-by-a-few-hours date on
    that rare failure is still better than the action failing outright."""
    try:
        return datetime.now(ZoneInfo(KUWAIT_TIMEZONE))
    except Exception:
        return datetime.now()


def kuwait_today() -> date:
    return kuwait_now().date()
