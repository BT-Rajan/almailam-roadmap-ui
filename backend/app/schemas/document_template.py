from datetime import datetime

from pydantic import BaseModel


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
