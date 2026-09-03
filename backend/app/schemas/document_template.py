from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class DocumentEmailRequest(BaseModel):
    # Defaults to the project's client email (see api/quotations.py's
    # and api/contracts.py's email_document endpoints) when omitted --
    # only needed to send somewhere else instead.
    toEmail: EmailStr | None = None


class DocumentTemplateOut(BaseModel):
    id: str
    documentType: str
    originalFilename: str
    fileSizeBytes: int
    isDefault: bool
    uploadedBy: str
    uploadedAt: datetime

    @staticmethod
    def from_model(template, uploaded_by_name: str) -> "DocumentTemplateOut":
        return DocumentTemplateOut(
            id=f"TPL-{template.id:03d}",
            documentType=template.document_type,
            originalFilename=template.original_filename,
            fileSizeBytes=template.file_size_bytes,
            isDefault=template.is_default,
            uploadedBy=uploaded_by_name,
            uploadedAt=template.created_at,
        )


class MergeFieldColumn(BaseModel):
    key: str
    label: str


class MergeField(BaseModel):
    """One entry from document_template_service.MERGE_FIELD_CATALOG --
    what the field-mapping screen's palette offers for a document type.
    kind is "text" (insert {{ key }} at a clicked spot), "repeating_table"
    (mark a table row as the repeating one, then place {{ loopVar.column
    }} per cell), or "repeating_list" (mark a paragraph as the repeating
    one, then place {{ loopVar }} in it)."""

    key: str
    label: str
    kind: str
    loopVar: str | None = None
    columns: list[MergeFieldColumn] | None = None


class TemplateCell(BaseModel):
    cellIndex: int
    text: str = ""


class TemplateRow(BaseModel):
    rowIndex: int
    cells: list[TemplateCell] = Field(default_factory=list)
    # Set on at most one row in the whole template -- see
    # document_template_service.apply_mapping.
    repeatingField: str | None = None


class TemplateBlock(BaseModel):
    """One paragraph or table from the template body, in document order.
    Used both for the extracted layout (GET .../layout) and for the
    admin's edited-back mapping (POST .../mapping) -- same shape either
    direction. `text`/`repeatingField` apply to a paragraph block; `rows`
    to a table block."""

    kind: str  # "paragraph" | "table"
    blockIndex: int
    text: str | None = None
    repeatingField: str | None = None
    rows: list[TemplateRow] | None = None


class TemplateLayout(BaseModel):
    blocks: list[TemplateBlock]


class TemplateMappingIn(BaseModel):
    blocks: list[TemplateBlock]
