from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.ai_config import AI_PROVIDER_IDS, AIConfiguration, AIProviderConfig, PromptTemplate
from app.services import audit_service

ENTITY_TYPE = "AI_CONFIGURATION"

DEFAULT_PROVIDER_LABELS = {"claude": "Claude", "deepseek": "DeepSeek"}

DEFAULT_PROMPT_TEMPLATES = [
    ("Project Status Summary", "Summarises a project's current status for stakeholders.", "Projects"),
    ("Document Review Checklist", "Reviews an uploaded document against required fields.", "Documents"),
    ("Contract Risk Highlights", "Surfaces notable clauses and risk areas in a contract.", "Contracts"),
    ("Government Form Guidance", "Explains a government form's requirements in plain language.", "Government Forms"),
    ("Client Update Draft", "Drafts a status update message for a client.", "Customer Communication"),
    ("Report Narrative", "Turns report figures into a short written narrative.", "Reports"),
]


def _ensure_seeded(db: Session) -> None:
    # Same race as role_service._ensure_seeded (see its own comment for
    # the full explanation) -- explicit id=1 / provider_id here means a
    # concurrent duplicate attempt hits a genuine primary/unique-key
    # IntegrityError rather than silently duplicating rows, so the same
    # catch-and-roll-back fix applies directly.
    try:
        if db.query(AIConfiguration).filter(AIConfiguration.id == 1).first() is None:
            db.add(AIConfiguration(id=1))
        for provider_id in AI_PROVIDER_IDS:
            if db.query(AIProviderConfig).filter(AIProviderConfig.provider_id == provider_id).first() is None:
                db.add(AIProviderConfig(provider_id=provider_id, label=DEFAULT_PROVIDER_LABELS[provider_id]))
        if db.query(PromptTemplate).first() is None:
            for name, description, module in DEFAULT_PROMPT_TEMPLATES:
                db.add(PromptTemplate(name=name, description=description, module=module, template=""))
        db.commit()
    except IntegrityError:
        db.rollback()


def get_configuration(db: Session) -> tuple[AIConfiguration, list[AIProviderConfig]]:
    _ensure_seeded(db)
    config = db.query(AIConfiguration).filter(AIConfiguration.id == 1).first()
    providers = db.query(AIProviderConfig).order_by(AIProviderConfig.id.asc()).all()
    return config, providers


def save_configuration(db: Session, payload, actor_id: int) -> tuple[AIConfiguration, list[AIProviderConfig]]:
    config, providers = get_configuration(db)
    audit_service.log_event(
        db, ENTITY_TYPE, config.id, "AI configuration updated", actor_id,
        previous_value=str(config.is_enabled), new_value=str(payload.isEnabled),
    )
    config.is_enabled = payload.isEnabled
    config.default_provider = payload.defaultProvider
    config.provider_priority = payload.providerPriority
    config.timeout_seconds = payload.timeoutSeconds
    config.max_tokens = payload.maxTokens
    config.temperature = payload.temperature
    config.cache_duration_minutes = payload.cacheDurationMinutes
    config.retry_limit = payload.retryLimit

    providers_by_id = {p.provider_id: p for p in providers}
    for provider_input in payload.providers:
        provider = providers_by_id.get(provider_input.id)
        if not provider:
            continue
        provider.label = provider_input.label
        provider.model = provider_input.model
        # apiKeyMasked arrives already masked by the client (see
        # AIProviderCard.vue) -- the raw key is never sent over the wire.
        # We only persist whether one has been provided and its hint.
        if provider_input.apiKeyMasked:
            provider.has_api_key = True
            provider.api_key_hint = provider_input.apiKeyMasked[-4:]

    db.commit()
    db.refresh(config)
    return config, db.query(AIProviderConfig).order_by(AIProviderConfig.id.asc()).all()


def list_prompt_templates(db: Session) -> list[PromptTemplate]:
    _ensure_seeded(db)
    return db.query(PromptTemplate).order_by(PromptTemplate.id.asc()).all()


def save_prompt_template(db: Session, raw_id: str, payload, actor_id: int) -> PromptTemplate:
    text = raw_id.removeprefix("PMT-") if raw_id.upper().startswith("PMT-") else raw_id
    if not text.isdigit():
        raise ValidationAppError("Invalid prompt template id.")
    template = db.query(PromptTemplate).filter(PromptTemplate.id == int(text)).first()
    if not template:
        raise NotFoundError("Prompt template")
    audit_service.log_event(db, ENTITY_TYPE, template.id, "Prompt template updated", actor_id, new_value=payload.name)
    template.name = payload.name
    template.description = payload.description
    template.module = payload.module
    template.template = payload.template
    db.commit()
    db.refresh(template)
    return template
