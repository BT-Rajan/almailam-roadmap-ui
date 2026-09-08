from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


def not_future_validator(label: str):
    """Field validator factory for a date that records when something
    was itself issued/dated/agreed (a Quotation's issue date, an
    identification document's issue date, a Financial Agreement's own
    agreement date) -- these are facts about the past or present, so a
    value after today is always a data-entry mistake, never a
    legitimate future plan. None-safe (returns None as-is) so the same
    factory works on both required and optional (Update-schema) fields
    -- a required field simply never reaches here as None, since
    Pydantic's own "field required" check already rejects that first."""

    def _check(value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError(f"{label} cannot be in the future")
        return value

    return _check


def not_past_validator(label: str):
    """Field validator factory for a date marking when something stops
    being valid (a Quotation's "valid till", a Contract's expiry, a
    Supervision activity's own end date) -- a value already in the past
    would mean creating something that's expired the moment it exists.
    None-safe, same reasoning as not_future_validator above."""

    def _check(value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError(f"{label} cannot be in the past")
        return value

    return _check


class ErrorResponse(BaseModel):
    error: str


class PagedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    pageSize: int
    totalPages: int


class ListParams(BaseModel):
    page: int = 1
    page_size: int = 25
    search: str | None = None
    status: str | None = None
    sort: str | None = None
