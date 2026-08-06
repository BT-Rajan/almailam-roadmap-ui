from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_config import (
    AIConfigurationIn,
    AIConfigurationOut,
    PromptTemplateIn,
    PromptTemplateOut,
    ProviderTestResult,
)
from app.schemas.ai_review import (
    AIAssistantContractIn,
    AIAssistantDocumentIn,
    AIAssistantPromptIn,
    AIAssistantRiskIn,
    AIInteractionOut,
)
from app.schemas.document import DocumentAIReviewOut
from app.services import ai_config_service, ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])

# AI configuration is Administration-level, same as company settings and
# workflow templates.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/configuration", response_model=AIConfigurationOut)
def get_configuration(db: Session = Depends(get_db), _=Depends(can_view)):
    config, providers = ai_config_service.get_configuration(db)
    return AIConfigurationOut.from_model(config, providers)


@router.post("/configuration", response_model=AIConfigurationOut)
def save_configuration(
    payload: AIConfigurationIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    config, providers = ai_config_service.save_configuration(db, payload, current_user.id)
    return AIConfigurationOut.from_model(config, providers)


@router.post("/providers/{provider_id}/test-connection", response_model=ProviderTestResult)
async def test_provider_connection(provider_id: str, db: Session = Depends(get_db), _=Depends(can_edit)):
    # Genuinely tests connectivity with a minimal real call now that
    # real provider integration exists (app/services/ai_service.py) --
    # still never fabricates a success. A real failure (no key, provider
    # error, timeout) is reported honestly with the real error text.
    from app.services.ai_service import _PROVIDER_CALLERS, AIUnavailableError

    caller = _PROVIDER_CALLERS.get(provider_id)
    if not caller:
        return ProviderTestResult(success=False, message=f"Unknown provider '{provider_id}'.")

    config, _providers = ai_config_service.get_configuration(db)
    try:
        await caller("Reply with exactly: OK", "Reply with exactly the word OK and nothing else.", 10, 0, 15)
        return ProviderTestResult(success=True, message="Connection successful.")
    except AIUnavailableError as exc:
        return ProviderTestResult(success=False, message=str(exc))
    except Exception as exc:  # noqa: BLE001 -- surfacing the real provider error is the point
        return ProviderTestResult(success=False, message=f"Connection failed: {exc}")


@router.get("/prompt-templates", response_model=list[PromptTemplateOut])
def list_prompt_templates(db: Session = Depends(get_db), _=Depends(can_view)):
    return [PromptTemplateOut.from_model(t) for t in ai_config_service.list_prompt_templates(db)]


@router.patch("/prompt-templates/{template_id}", response_model=PromptTemplateOut)
def save_prompt_template(
    template_id: str,
    payload: PromptTemplateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    template = ai_config_service.save_prompt_template(db, template_id, payload, current_user.id)
    return PromptTemplateOut.from_model(template)


def _to_interaction(prompt: str, provider: str, template_name: str | None, result: dict) -> AIInteractionOut:
    from datetime import datetime, timezone
    from uuid import uuid4

    return AIInteractionOut(
        id=str(uuid4()),
        prompt=prompt,
        templateName=template_name,
        provider=provider,
        summary=result["summary"],
        details=result["details"],
        confidence=result["confidence"],
        suggestedActions=result["suggestedActions"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/assistant/response", response_model=AIInteractionOut)
async def assistant_response(
    payload: AIAssistantPromptIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        result = await ai_service.assistant_response(db, payload.prompt)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_interaction(payload.prompt, payload.provider or "claude", payload.template_name, result)


@router.post("/assistant/analyze-contract", response_model=AIInteractionOut)
async def assistant_analyze_contract(
    payload: AIAssistantContractIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    from app.models.project import Project
    from app.services import contract_service

    contract = contract_service.get_contract(db, payload.contract_id)
    clauses = contract_service.get_clauses(db, contract.id)
    project = db.query(Project).filter(Project.id == contract.project_id).first()
    try:
        result = await ai_service.assistant_analyze_contract(db, contract, clauses, project)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_interaction(f"Analyze contract {payload.contract_id}", "claude", None, result)


@router.post("/assistant/review-document", response_model=AIInteractionOut)
async def assistant_review_document(
    payload: AIAssistantDocumentIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    from app.models.project import Project
    from app.services import document_service

    document = document_service.get_document(db, payload.document_id)
    project = db.query(Project).filter(Project.id == document.project_id).first()
    try:
        result = await ai_service.assistant_review_document(db, document, project)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_interaction(f"Review document {payload.document_id}", "claude", None, result)


@router.post("/assistant/assess-risk", response_model=AIInteractionOut)
async def assistant_assess_risk(
    payload: AIAssistantRiskIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    description = f"{payload.entity_type} {payload.entity_id}"
    try:
        result = await ai_service.assistant_assess_risk(db, description)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_interaction(f"Assess risk for {description}", "claude", None, result)


@router.get("/documents/{document_no}/review", response_model=DocumentAIReviewOut)
async def get_document_review(
    document_no: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    from app.models.project import Project
    from app.services import document_service

    document = document_service.get_document(db, document_no)
    project = db.query(Project).filter(Project.id == document.project_id).first()
    try:
        return await ai_service.get_document_review(db, document, project, actor_id=current_user.id)
    except ai_service.AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
