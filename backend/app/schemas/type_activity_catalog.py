from pydantic import BaseModel, Field, condecimal


class TypeActivityItemOut(BaseModel):
    id: str
    name: str
    cost: float

    @staticmethod
    def from_model(item) -> "TypeActivityItemOut":
        return TypeActivityItemOut(
            id=f"TAI-{item.id:03d}",
            name=item.name,
            cost=float(item.cost),
        )


class TypeActivityCategoryOut(BaseModel):
    id: str
    name: str
    activities: list[TypeActivityItemOut]

    @staticmethod
    def from_model(category) -> "TypeActivityCategoryOut":
        return TypeActivityCategoryOut(
            id=f"TAC-{category.id:03d}",
            name=category.name,
            activities=[TypeActivityItemOut.from_model(a) for a in category.activities],
        )


class TypeActivityCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class TypeActivityCategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class TypeActivityItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    cost: condecimal(ge=0, max_digits=12, decimal_places=2) = Field(default=0)  # type: ignore[valid-type]


class TypeActivityItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    cost: condecimal(ge=0, max_digits=12, decimal_places=2) | None = None  # type: ignore[valid-type]


class ProjectSelectedTypeActivityOut(BaseModel):
    id: str
    activityName: str
    cost: float
    isCoveredByService: bool
    isComplete: bool = False

    @staticmethod
    def from_model(row) -> "ProjectSelectedTypeActivityOut":
        return ProjectSelectedTypeActivityOut(
            id=row.type_activity_item_id,
            activityName=row.activity_name,
            cost=float(row.cost),
            isCoveredByService=row.is_covered_by_service,
            isComplete=row.is_complete,
        )


class ProjectTypeActivitySelectionIn(BaseModel):
    """What the New Project wizard's final-step modal submits: the
    category picked, and which of its activities were checked."""

    categoryId: str
    activityIds: list[str] = Field(default_factory=list)
