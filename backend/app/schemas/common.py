from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str


class OtpVerifyRequest(BaseModel):
    """Shared by every email-OTP verification endpoint -- client
    onboarding (POST /api/clients/{id}/onboarding-state/verify-otp) and
    project Requirement confirmation (POST /api/projects/{project_no}/
    requirement/verify-otp) both take just the code the client read back."""

    code: str = Field(min_length=1, max_length=12)


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
