"""The reporting period shared by every date-ranged report.

A period is an inclusive pair of Kuwait calendar dates. Date columns
(payment_date, due_date, signed_date, ...) compare against those dates
directly; timestamp columns (created_at, audit_log.changed_at) are stored
in UTC by the database, so they compare against the UTC instants of
Kuwait midnight at each end -- Kuwait is UTC+3 all year (no DST).
"""

from bisect import bisect_right
from calendar import month_abbr
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.core.exceptions import ValidationAppError

KUWAIT_UTC_OFFSET = timedelta(hours=3)
# Long enough for a multi-year trend; short enough that a typo like
# 1026-01-01 can't make one request scan and bucket a thousand years.
MAX_PERIOD_DAYS = 366 * 10
DAILY_UP_TO_DAYS = 14
WEEKLY_UP_TO_DAYS = 62
MONTHLY_UP_TO_MONTHS = 36


@dataclass(frozen=True)
class Bucket:
    label: str
    start: date
    end: date  # inclusive


@dataclass(frozen=True)
class Period:
    start: date
    end: date  # inclusive

    @property
    def utc_start(self) -> datetime:
        """00:00 Kuwait on the first day, as naive UTC."""
        return datetime.combine(self.start, time.min) - KUWAIT_UTC_OFFSET

    @property
    def utc_end_exclusive(self) -> datetime:
        """00:00 Kuwait on the day after the last day, as naive UTC."""
        return datetime.combine(self.end + timedelta(days=1), time.min) - KUWAIT_UTC_OFFSET

    def as_dict(self) -> dict:
        return {"startDate": self.start.isoformat(), "endDate": self.end.isoformat()}


def make_period(start: date, end: date) -> Period:
    if start > end:
        raise ValidationAppError("The period's start date must be on or before its end date.")
    if (end - start).days > MAX_PERIOD_DAYS:
        raise ValidationAppError("The period can't be longer than 10 years.")
    return Period(start, end)


def kuwait_date(utc_timestamp: datetime) -> date:
    """The Kuwait calendar date of a naive-UTC timestamp from the database."""
    return (utc_timestamp + KUWAIT_UTC_OFFSET).date()


def _add_months(year: int, month: int, count: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + count
    return index // 12, index % 12 + 1


def granularity(period: Period) -> str:
    """'day', 'week', 'month' or 'year' -- the bucket size buckets() uses."""
    if (period.end - period.start).days + 1 <= DAILY_UP_TO_DAYS:
        return "day"
    if (period.end - period.start).days + 1 <= WEEKLY_UP_TO_DAYS:
        return "week"
    months = (period.end.year - period.start.year) * 12 + period.end.month - period.start.month + 1
    return "month" if months <= MONTHLY_UP_TO_MONTHS else "year"


def buckets(period: Period) -> list[Bucket]:
    """Chart buckets for the period: days for up to two weeks, weeks for
    up to ~2 months, months for up to 3 years, years beyond that. The first
    and last buckets are clipped to the period, so every bucket only counts
    in-period days."""
    days = (period.end - period.start).days + 1
    result: list[Bucket] = []
    if days <= DAILY_UP_TO_DAYS:
        for offset in range(days):
            day = period.start + timedelta(days=offset)
            result.append(Bucket(f"{day.day} {month_abbr[day.month]}", day, day))
        return result
    if days <= WEEKLY_UP_TO_DAYS:
        cursor = period.start
        while cursor <= period.end:
            last = min(cursor + timedelta(days=6), period.end)
            result.append(Bucket(f"{cursor.day} {month_abbr[cursor.month]}", cursor, last))
            cursor = last + timedelta(days=1)
        return result

    months = (period.end.year - period.start.year) * 12 + period.end.month - period.start.month + 1
    if months <= MONTHLY_UP_TO_MONTHS:
        year, month = period.start.year, period.start.month
        for _ in range(months):
            first = date(year, month, 1)
            next_year, next_month = _add_months(year, month, 1)
            last = date(next_year, next_month, 1) - timedelta(days=1)
            result.append(Bucket(f"{month_abbr[month]} {year}", max(first, period.start), min(last, period.end)))
            year, month = next_year, next_month
        return result

    for year in range(period.start.year, period.end.year + 1):
        result.append(Bucket(str(year), max(date(year, 1, 1), period.start), min(date(year, 12, 31), period.end)))
    return result


def bucketer(bucket_list: list[Bucket]):
    """A `date -> bucket index | None` lookup (None outside the period).
    Buckets are contiguous and sorted, so a binary search on their starts."""
    starts = [bucket.start for bucket in bucket_list]

    def index_of(day: date) -> int | None:
        index = bisect_right(starts, day) - 1
        if index < 0 or day > bucket_list[index].end:
            return None
        return index

    return index_of
