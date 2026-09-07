from pydantic import BaseModel, Field


class PermitCatalogItemOut(BaseModel):
    id: str
    name: str

    @staticmethod
    def from_model(permit) -> "PermitCatalogItemOut":
        return PermitCatalogItemOut(id=f"PER-{permit.id:03d}", name=permit.name)


class PermitCatalogItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class PermitCatalogItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


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
