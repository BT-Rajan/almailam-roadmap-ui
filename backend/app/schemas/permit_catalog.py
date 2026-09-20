from typing import Annotated

from pydantic import BaseModel, Field, condecimal


class PermitCatalogItemOut(BaseModel):
    id: str
    name: str
    fixedCost: float
    # Application setup (migration 0109). requiredDocuments is the override
    # only -- None means the form's own list applies.
    authorityId: str | None = None
    formId: str | None = None
    requiredDocuments: list[str] | None = None

    @staticmethod
    def from_model(
        permit, valid_setup: tuple[set[int], set[int]] | None = None
    ) -> "PermitCatalogItemOut":
        # valid_setup (permit_catalog_service.valid_setup_ids) hides an
        # authority/form that has since been deleted or archived, so the
        # permit reads as not configured instead of pointing at a dead form.
        authority_id, form_id = permit.authority_id, permit.form_id
        if valid_setup is not None and (authority_id not in valid_setup[0] or form_id not in valid_setup[1]):
            authority_id = form_id = None
        return PermitCatalogItemOut(
            id=f"PER-{permit.id:03d}",
            name=permit.name,
            fixedCost=float(permit.fixed_cost),
            authorityId=f"AUTH-{authority_id:03d}" if authority_id and form_id else None,
            formId=f"FORM-{form_id:03d}" if authority_id and form_id else None,
            requiredDocuments=list(permit.required_documents) if authority_id and permit.required_documents else None,
        )


class PermitCatalogItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) = 0  # type: ignore[valid-type]


class PermitCatalogItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) = 0  # type: ignore[valid-type]


class PermitPrerequisiteOut(BaseModel):
    """One admin-configured "this Design activity must be Complete
    before the permit is eligible" rule (migration 0073) -- see
    project_service._recompute_permit_eligibility."""

    id: str
    designActivityId: str
    designActivityName: str
    serviceName: str

    @staticmethod
    def from_model(prerequisite) -> "PermitPrerequisiteOut":
        activity = prerequisite.design_activity
        return PermitPrerequisiteOut(
            id=str(prerequisite.id),
            designActivityId=f"ACT-{activity.id:03d}",
            designActivityName=activity.name,
            serviceName=activity.service.name,
        )


class PermitPrerequisiteCreate(BaseModel):
    designActivityId: str = Field(min_length=1, max_length=20)


class PermitApplicationSetupUpdate(BaseModel):
    """Replaces a permit type's application setup as a whole. Send
    authorityId and formId together (or both null to unmap);
    requiredDocuments null/empty falls back to the form's own list."""

    authorityId: str | None = Field(default=None, max_length=20)
    formId: str | None = Field(default=None, max_length=20)
    requiredDocuments: list[Annotated[str, Field(min_length=1, max_length=150)]] | None = Field(
        default=None, max_length=50
    )
