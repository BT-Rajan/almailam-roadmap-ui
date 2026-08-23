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
