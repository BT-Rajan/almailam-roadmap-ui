from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_config import AIConfigurationIn, AIConfigurationOut, ProviderTestResult
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
async def test_provider_connection(provider_id: str, db: Session = Depends(get_db), _=Depends(can_edit)):
    # Genuinely tests connectivity with a minimal real call -- never
    # fabricates a success. A real failure (no key, provider error,
    # timeout) is reported honestly with the real error text.
    from app.services.ai_service import _PROVIDER_CALLERS, AIUnavailableError

    caller = _PROVIDER_CALLERS.get(provider_id)
    if not caller:
        return ProviderTestResult(success=False, message=f"Unknown provider '{provider_id}'.")

    _config, providers = ai_config_service.get_configuration(db)
    provider = next((p for p in providers if p.provider_id == provider_id), None)

    try:
        await caller("Reply with exactly: OK", "Reply with exactly the word OK and nothing else.", 10, 0, 15, provider)
        return ProviderTestResult(success=True, message="Connection successful.")
    except AIUnavailableError as exc:
        return ProviderTestResult(success=False, message=str(exc))
    except Exception as exc:  # noqa: BLE001 -- surfacing the real provider error is the point
        return ProviderTestResult(success=False, message=f"Connection failed: {exc}")
