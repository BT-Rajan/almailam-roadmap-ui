from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str


class PagedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ListParams(BaseModel):
    page: int = 1
    page_size: int = 25
    search: str | None = None
    status: str | None = None
    sort: str | None = None
