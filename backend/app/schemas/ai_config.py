from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.ai_config import DEFAULT_KB_SYSTEM_PROMPT

AI_PROVIDER_IDS = ("claude", "deepseek")

# The real, live-usable credential for each provider is an environment
# variable on the server (see app.core.config.Settings, app.services.
# ai_service) -- never the "API key" typed into the admin form below.
# AIProviderConfig.has_api_key/api_key_hint only remembers that an admin
# once typed *something* in for their own bookkeeping (the raw value is
# masked client-side in AIProviderCard.vue before it's ever sent, so the
# server never even sees it) -- it is not proof the provider will actually
# work. `status` here must reflect the environment variable, or an admin
# who has typed a key sees "Connected" while every real call (and Test
# Connection) honestly fails with "API key is not configured on the
# server," which is exactly the bug this was fixed to stop reproducing.
_PROVIDER_ENV_KEY_ATTR = {"claude": "ANTHROPIC_API_KEY", "deepseek": "DEEPSEEK_API_KEY"}


class AIProviderConfigOut(BaseModel):
    id: str
    label: str
    model: str
    apiKeyMasked: str
    # Reflects whether the server environment actually has a usable key
    # for this provider (see _PROVIDER_ENV_KEY_ATTR above), not whether an
    # admin has typed something into this form -- see testProviderConnection
    # for the live, definitive check.
    status: str

    @staticmethod
    def from_model(provider) -> "AIProviderConfigOut":
        settings = get_settings()
        env_attr = _PROVIDER_ENV_KEY_ATTR.get(provider.provider_id)
        has_env_key = bool(env_attr and getattr(settings, env_attr, ""))
        return AIProviderConfigOut(
            id=provider.provider_id,
            label=provider.label,
            model=provider.model,
            apiKeyMasked=(f"••••••••{provider.api_key_hint}" if provider.has_api_key else ""),
            status="connected" if has_env_key else "not-configured",
        )


class AIProviderConfigIn(BaseModel):
    id: str
    label: str = Field(max_length=80)
    model: str = Field(default="", max_length=120)
    apiKeyMasked: str = Field(default="", max_length=20)


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
