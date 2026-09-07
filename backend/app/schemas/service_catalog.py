from typing import Literal

from pydantic import BaseModel, Field, condecimal


class ServiceCatalogActivityOut(BaseModel):
    id: str
    name: str
    fixedCost: float

    @staticmethod
    def from_model(activity) -> "ServiceCatalogActivityOut":
        return ServiceCatalogActivityOut(
            id=f"ACT-{activity.id:03d}",
            name=activity.name,
            fixedCost=float(activity.fixed_cost),
        )


class ServiceCatalogItemOut(BaseModel):
    id: str
    name: str
    branch: Literal["Design", "Supervision"]
    activities: list[ServiceCatalogActivityOut]

    @staticmethod
    def from_model(service) -> "ServiceCatalogItemOut":
        return ServiceCatalogItemOut(
            id=f"SVC-{service.id:03d}",
            name=service.name,
            branch=service.branch,
            activities=[ServiceCatalogActivityOut.from_model(a) for a in service.activities],
        )


class ServiceCatalogItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    branch: Literal["Design", "Supervision"] = "Design"


class ServiceCatalogItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ServiceCatalogActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) = Field(default=0)  # type: ignore[valid-type]


class ServiceCatalogActivityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) | None = None  # type: ignore[valid-type]


class SupervisionPrerequisiteOut(BaseModel):
    """One admin-configured "this Design activity must be Complete
    before this Supervision activity is eligible" rule (migration
    0074) -- see project_service._recompute_supervision_eligibility.
    Same shape as PermitPrerequisiteOut."""

    id: str
    designActivityId: str
    designActivityName: str
    serviceName: str

    @staticmethod
    def from_model(prerequisite) -> "SupervisionPrerequisiteOut":
        activity = prerequisite.design_activity
        return SupervisionPrerequisiteOut(
            id=str(prerequisite.id),
            designActivityId=f"ACT-{activity.id:03d}",
            designActivityName=activity.name,
            serviceName=activity.service.name,
        )


class SupervisionPrerequisiteCreate(BaseModel):
    designActivityId: str = Field(min_length=1, max_length=20)
