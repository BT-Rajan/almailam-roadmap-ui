from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.security import decrypt_secret
from app.models.ai_config import DEFAULT_KB_SYSTEM_PROMPT

AI_PROVIDER_IDS = ("claude", "deepseek")

# The environment variable fallback for each provider, read only when no
# key has been saved from the admin form (see AIProviderConfig.
# api_key_encrypted). Used both to resolve `status` below and by
# app.services.ai_service at call time -- keep these in sync.
PROVIDER_ENV_KEY_ATTR = {"claude": "ANTHROPIC_API_KEY", "deepseek": "DEEPSEEK_API_KEY"}


def provider_has_usable_key(provider) -> bool:
    """True if this provider can actually be called right now -- a saved,
    decryptable admin key, or (failing that) the environment variable
    fallback. Matches exactly what app.services.ai_service resolves at
    call time, so `status` here is never out of sync with reality."""
    if provider.api_key_encrypted and decrypt_secret(provider.api_key_encrypted):
        return True
    env_attr = PROVIDER_ENV_KEY_ATTR.get(provider.provider_id)
    return bool(env_attr and getattr(get_settings(), env_attr, ""))


class AIProviderConfigOut(BaseModel):
    id: str
    label: str
    model: str
    apiKeyMasked: str
    # Reflects whether a live call can actually be made for this provider
    # right now (see provider_has_usable_key above) -- not merely whether
    # an admin has typed something into this form. See testProviderConnection
    # for the live, definitive check.
    status: str

    @staticmethod
    def from_model(provider) -> "AIProviderConfigOut":
        return AIProviderConfigOut(
            id=provider.provider_id,
            label=provider.label,
            model=provider.model,
            apiKeyMasked=(f"••••••••{provider.api_key_hint}" if provider.has_api_key else ""),
            status="connected" if provider_has_usable_key(provider) else "not-configured",
        )


class AIProviderConfigIn(BaseModel):
    id: str
    label: str = Field(max_length=80)
    model: str = Field(default="", max_length=120)
    # Raw key, sent once over HTTPS when an admin sets/changes it --
    # encrypted immediately on the way into storage (see
    # ai_config_service.save_configuration) and never stored or logged in
    # plaintext. None/empty means "leave the currently saved key (if any)
    # untouched," not "clear it."
    apiKey: str | None = Field(default=None, max_length=200)


class AIConfigurationOut(BaseModel):
    isEnabled: bool
    defaultProvider: str
    providerPriority: list[str]
    timeoutSeconds: int
    maxTokens: int
    temperature: float
    cacheDurationMinutes: int
    retryLimit: int
    kbSystemPrompt: str
    # Lets the admin UI offer a "Reset to Default" action without having
    # the default prompt text hardcoded twice (once here, once in the
    # frontend) and drifting out of sync.
    kbDefaultSystemPrompt: str
    kbMaxUploadSizeMb: int
    kbMaxDocumentChars: int
    kbMaxContextChars: int
    providers: list[AIProviderConfigOut]

    @staticmethod
    def from_model(config, providers) -> "AIConfigurationOut":
        return AIConfigurationOut(
            isEnabled=config.is_enabled,
            defaultProvider=config.default_provider,
            providerPriority=config.provider_priority,
            timeoutSeconds=config.timeout_seconds,
            maxTokens=config.max_tokens,
            temperature=config.temperature,
            cacheDurationMinutes=config.cache_duration_minutes,
            retryLimit=config.retry_limit,
            kbSystemPrompt=config.kb_system_prompt or DEFAULT_KB_SYSTEM_PROMPT,
            kbDefaultSystemPrompt=DEFAULT_KB_SYSTEM_PROMPT,
            kbMaxUploadSizeMb=config.kb_max_upload_size_mb,
            kbMaxDocumentChars=config.kb_max_document_chars,
            kbMaxContextChars=config.kb_max_context_chars,
            providers=[AIProviderConfigOut.from_model(p) for p in providers],
        )


class AIConfigurationIn(BaseModel):
    isEnabled: bool
    defaultProvider: str
    providerPriority: list[str]
    timeoutSeconds: int = Field(ge=1, le=300)
    maxTokens: int = Field(ge=1, le=100_000)
    temperature: float = Field(ge=0, le=2)
    cacheDurationMinutes: int = Field(ge=0, le=1440)
    retryLimit: int = Field(ge=0, le=10)
    kbSystemPrompt: str = Field(min_length=1, max_length=8000)
    kbMaxUploadSizeMb: int = Field(ge=1, le=100)
    kbMaxDocumentChars: int = Field(ge=1000, le=1_000_000)
    kbMaxContextChars: int = Field(ge=1000, le=2_000_000)
    providers: list[AIProviderConfigIn]


class ProviderTestResult(BaseModel):
    success: bool
    message: str
