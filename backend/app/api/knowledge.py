from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.file_storage import format_file_size
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeAskIn,
    KnowledgeAskOut,
    KnowledgeDocumentOut,
    KnowledgeDocumentUpdate,
    KnowledgeStatusOut,
)
from app.services import ai_config_service, ai_service, knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

can_view = require_permission("Knowledgebase", "view")
can_edit = require_permission("Knowledgebase", "edit")
can_delete = require_permission("Knowledgebase", "delete")


@router.get("/status", response_model=KnowledgeStatusOut)
def get_status(db: Session = Depends(get_db), _=Depends(can_view)):
    # Deliberately not the full /api/ai/configuration -- see
    # KnowledgeStatusOut's docstring. Any user who can see the Knowledge
    # Base at all needs this to know whether to show the sparkle icon/
    # chat drawer and the ask panel as enabled, without needing
    # Administration access.
    config, _providers = ai_config_service.get_configuration(db)
    return KnowledgeStatusOut(isEnabled=config.is_enabled)


@router.get("/documents", response_model=list[KnowledgeDocumentOut])
def list_documents(db: Session = Depends(get_db), _=Depends(can_view)):
    documents = knowledge_service.list_documents(db)
    uploader_ids = {d.uploaded_by for d in documents}
    names = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(uploader_ids)).all()} if uploader_ids else {}
    return [
        KnowledgeDocumentOut.from_model(d, names.get(d.uploaded_by, "Unknown"), format_file_size(d.file_size_bytes))
        for d in documents
    ]


@router.post("/documents", response_model=KnowledgeDocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = knowledge_service.upload_document(db, file, title, current_user)
    return KnowledgeDocumentOut.from_model(document, current_user.full_name, format_file_size(document.file_size_bytes))


@router.patch("/documents/{document_no}", response_model=KnowledgeDocumentOut)
def update_document(
    document_no: str,
    payload: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = knowledge_service.set_active(db, document_no, payload.isActive, current_user)
    uploader = db.query(User).filter(User.id == document.uploaded_by).first()
    return KnowledgeDocumentOut.from_model(
        document, uploader.full_name if uploader else "Unknown", format_file_size(document.file_size_bytes)
    )


@router.delete("/documents/{document_no}", status_code=204)
def delete_document(document_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    knowledge_service.delete_document(db, document_no, current_user)


@router.post("/ask", response_model=KnowledgeAskOut)
async def ask(payload: KnowledgeAskIn, db: Session = Depends(get_db), current_user: User = Depends(can_view)):
    try:
        result = await knowledge_service.ask_question(db, payload.documentId, payload.question)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return KnowledgeAskOut(**result)
