from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentOut(BaseModel):
    id: str
    title: str
    originalFilename: str
    fileSize: str
    contentType: str
    charCount: int
    truncated: bool
    extractionOk: bool
    extractionError: str
    isActive: bool
    uploadedBy: str
    createdAt: datetime

    @staticmethod
    def from_model(document, uploaded_by_name: str, file_size_display: str) -> "KnowledgeDocumentOut":
        return KnowledgeDocumentOut(
            id=document.document_no,
            title=document.title,
            originalFilename=document.original_filename,
            fileSize=file_size_display,
            contentType=document.content_type,
            charCount=document.char_count,
            truncated=document.truncated,
            extractionOk=document.extraction_ok,
            extractionError=document.extraction_error,
            isActive=document.is_active,
            uploadedBy=uploaded_by_name,
            createdAt=document.created_at,
        )


class KnowledgeDocumentUpdate(BaseModel):
    isActive: bool


class KnowledgeAskIn(BaseModel):
    documentId: str | None = Field(default=None, description="Ask against one document, or omit for all active documents.")
    question: str = Field(min_length=1, max_length=2000)


class KnowledgeAskOut(BaseModel):
    answer: str
    sourceDocumentIds: list[str]
    cached: bool
