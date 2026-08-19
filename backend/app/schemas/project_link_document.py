from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.document import PROJECT_LINK_DOCUMENT_CATEGORIES


class ProjectLinkDocumentOut(BaseModel):
    id: str
    projectId: str
    category: str
    name: str
    path: str
    addedBy: str
    addedDate: date

    @staticmethod
    def from_model(document, project_no: str, added_by_name: str) -> "ProjectLinkDocumentOut":
        return ProjectLinkDocumentOut(
            id=document.link_document_no,
            projectId=project_no,
            category=document.category,
            name=document.name,
            path=document.path,
            addedBy=added_by_name,
            addedDate=document.added_date,
        )


class ProjectLinkDocumentCreate(BaseModel):
    category: str
    name: str = Field(min_length=1, max_length=200)
    # A link back to where the file actually lives (shared drive, government
    # portal, network path, etc.) -- not a file upload. Accepts either a URL
    # or an absolute filesystem/UNC-style path so it fits how the office
    # actually stores these outside the app.
    path: str = Field(min_length=1, max_length=1000)

    @field_validator("category")
    @classmethod
    def _check_category(cls, value: str) -> str:
        if value not in PROJECT_LINK_DOCUMENT_CATEGORIES:
            raise ValueError(f"category must be one of {PROJECT_LINK_DOCUMENT_CATEGORIES}")
        return value

    @field_validator("path")
    @classmethod
    def _check_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("path is required.")
        return value
