from pydantic import BaseModel, Field, field_validator

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


def provider_key_is_unreadable(provider) -> bool:
    """True specifically when a key WAS saved (has_api_key) but no longer
    decrypts (e.g. the server's encryption key has rotated since) --
    distinct from simply never having had one entered. Without this,
    apiKeyMasked below keeps showing a normal-looking "••••••••1234" (a
    persisted display flag, never re-derived) at the same time status
    flips to not-configured, with nothing to tell an admin *why* a
    provider that looks configured suddenly can't be used."""
    return bool(provider.has_api_key and provider.api_key_encrypted and not decrypt_secret(provider.api_key_encrypted))


class AIProviderConfigOut(BaseModel):
    id: str
    label: str
    model: str
    apiKeyMasked: str
    keyUnreadable: bool
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
            keyUnreadable=provider_key_is_unreadable(provider),
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

    # Every other tunable on this schema has Field-level bounds; these two
    # don't, since they're not a range but a membership check against the
    # real provider list. Without this, a defaultProvider/providerPriority
    # naming an unknown id would save successfully but make
    # ai_service.generate_text's provider loop skip it silently -- with
    # both fields wrong at once, every configured API key becomes
    # unreachable with no indication why (a generic "No AI provider is
    # configured" even though keys are saved and valid). The admin UI
    # can't produce this today (its SelectBox is populated from the real
    # provider list) but this schema is also the contract for anything
    # else calling POST /api/ai/configuration directly.
    @field_validator("defaultProvider")
    @classmethod
    def default_provider_must_be_known(cls, value: str) -> str:
        if value not in AI_PROVIDER_IDS:
            raise ValueError(f"defaultProvider must be one of {AI_PROVIDER_IDS}")
        return value

    @field_validator("providerPriority")
    @classmethod
    def provider_priority_must_be_known(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("providerPriority must not be empty")
        unknown = [provider_id for provider_id in value if provider_id not in AI_PROVIDER_IDS]
        if unknown:
            raise ValueError(f"providerPriority contains unknown provider id(s): {unknown}")
        return value


class ProviderTestResult(BaseModel):
    success: bool
    message: str
