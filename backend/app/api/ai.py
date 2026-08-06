from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_config import (
    AIConfigurationIn,
    AIConfigurationOut,
    PromptTemplateIn,
    PromptTemplateOut,
    ProviderTestResult,
)
from app.services import ai_config_service

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
def test_provider_connection(provider_id: str, _=Depends(can_edit)):
    # Honest by design: this environment has no live integration with any
    # AI provider, so this never fabricates a success or a specific
    # failure reason -- it says plainly that no connection was attempted.
    return ProviderTestResult(
        success=False,
        message="Live provider connection testing isn't available in this environment yet.",
    )


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
