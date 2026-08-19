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
    activities: list[ServiceCatalogActivityOut]

    @staticmethod
    def from_model(service) -> "ServiceCatalogItemOut":
        return ServiceCatalogItemOut(
            id=f"SVC-{service.id:03d}",
            name=service.name,
            activities=[ServiceCatalogActivityOut.from_model(a) for a in service.activities],
        )


class ServiceCatalogItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ServiceCatalogItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ServiceCatalogActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) = Field(default=0)  # type: ignore[valid-type]


class ServiceCatalogActivityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2) | None = None  # type: ignore[valid-type]
