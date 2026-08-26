from pydantic import BaseModel, Field

from app.models.ai_config import DEFAULT_KB_SYSTEM_PROMPT

AI_PROVIDER_IDS = ("claude", "deepseek")


class AIProviderConfigOut(BaseModel):
    id: str
    label: str
    model: str
    apiKeyMasked: str
    # Honest by construction: this reflects whether a key has been saved,
    # not whether it has been verified against a live provider. See
    # testProviderConnection for an explicit, honest "not yet implemented"
    # response rather than a fabricated success/failure.
    status: str

    @staticmethod
    def from_model(provider) -> "AIProviderConfigOut":
        return AIProviderConfigOut(
            id=provider.provider_id,
            label=provider.label,
            model=provider.model,
            apiKeyMasked=(f"••••••••{provider.api_key_hint}" if provider.has_api_key else ""),
            status="connected" if provider.has_api_key else "not-configured",
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
