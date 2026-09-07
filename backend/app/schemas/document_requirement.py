from pydantic import BaseModel, Field, field_validator

from app.models.document_requirement import DOCUMENT_REQUIREMENT_TARGET_TYPES


class DocumentRequirementOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    @staticmethod
    def from_model(requirement) -> "DocumentRequirementOut":
        return DocumentRequirementOut(id=str(requirement.id), name=requirement.name, description=requirement.description)


class DocumentRequirementCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class DocumentRequirementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class DocumentRequirementLinkOut(BaseModel):
    """One "this document is typically needed for this activity/permit"
    link (migration 0073) -- informational only, never enforced against
    task/activity closure. requirementName/requirementDescription are
    denormalized here so a target's reference checklist (Design/Permit/
    Supervision tab) doesn't need a second round trip per link."""

    id: str
    requirementId: str
    requirementName: str
    requirementDescription: str | None = None
    targetType: str
    targetCatalogId: str

    @staticmethod
    def from_model(link, requirement) -> "DocumentRequirementLinkOut":
        return DocumentRequirementLinkOut(
            id=str(link.id),
            requirementId=str(requirement.id),
            requirementName=requirement.name,
            requirementDescription=requirement.description,
            targetType=link.target_type,
            targetCatalogId=str(link.target_catalog_id),
        )


class DocumentRequirementLinkCreate(BaseModel):
    requirementId: str
    targetType: str
    # The catalog's own display id -- "ACT-004" for Design/Supervision,
    # "PER-003" for Permit -- resolved server-side against the right
    # catalog depending on targetType.
    targetCatalogId: str = Field(min_length=1, max_length=20)

    @field_validator("targetType")
    @classmethod
    def check_target_type(cls, value: str) -> str:
        if value not in DOCUMENT_REQUIREMENT_TARGET_TYPES:
            raise ValueError(f"targetType must be one of {DOCUMENT_REQUIREMENT_TARGET_TYPES}")
        return value
