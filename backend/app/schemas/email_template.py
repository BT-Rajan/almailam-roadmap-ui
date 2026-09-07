from datetime import datetime

from pydantic import BaseModel, Field


class EmailMergeField(BaseModel):
    """One entry from email_template_service.MERGE_FIELD_CATALOG -- what
    the admin's Templates panel offers as available {{ field }} tokens
    for one email key."""

    key: str
    label: str


class EmailTemplateOut(BaseModel):
    key: str
    subject: str
    body: str
    updatedBy: str
    updatedAt: datetime

    @staticmethod
    def from_model(template, updated_by_name: str) -> "EmailTemplateOut":
        return EmailTemplateOut(
            key=template.key,
            subject=template.subject,
            body=template.body,
            updatedBy=updated_by_name,
            updatedAt=template.updated_at,
        )


class EmailTemplateUpdate(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
