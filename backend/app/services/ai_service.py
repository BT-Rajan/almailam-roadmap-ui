"""Real LLM integration layer.

Every AI feature in this app -- currently just the knowledgebase Q&A tool --
goes through generate_text() below, which calls a real provider's API using
a real API key -- never a fabricated response. If no key is configured, or
AI is disabled in AI Configuration, this raises AIUnavailableError, and
every caller in this module turns that into a clear "not available" result
rather than making something up.

Two providers are supported, matching AI_PROVIDER_IDS in
app.models.ai_config: Anthropic (Claude) and DeepSeek. For each, the
credential/model actually used is resolved by _resolve_credentials()
below: the admin-saved, encrypted key/model on that provider's
AIProviderConfig row (set from the Knowledgebase AI admin page) takes
priority, falling back to the ANTHROPIC_API_KEY/DEEPSEEK_API_KEY server
environment variables. This means a key entered from the admin UI is live
immediately -- no server access or restart required -- while a deployment
that would rather fix credentials at the infrastructure level can still
do so via the environment.
"""

import httpx

from app.core.config import get_settings
from app.core.security import decrypt_secret
from app.services import ai_config_service


class AIUnavailableError(Exception):
    """Raised when AI features are disabled, unconfigured, or a live call
    fails -- callers must turn this into an honest 'unavailable' response,
    never fall back to fabricated content."""


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def _resolve_credentials(provider, env_key_attr: str, env_model_attr: str) -> tuple[str, str]:
    """Returns (api_key, model) for a provider row (or None, if nothing is
    saved for it yet). See module docstring for the precedence."""
    settings = get_settings()
    api_key = ""
    if provider is not None and provider.api_key_encrypted:
        api_key = decrypt_secret(provider.api_key_encrypted)
    if not api_key:
        api_key = getattr(settings, env_key_attr, "") or ""
    model = (provider.model.strip() if provider is not None and provider.model else "") or getattr(
        settings, env_model_attr, ""
    )
    return api_key, model


async def _call_anthropic(
    prompt: str, system: str, max_tokens: int, temperature: float, timeout: int, provider=None
) -> str:
    api_key, model = _resolve_credentials(provider, "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL")
    if not api_key:
        raise AIUnavailableError("Anthropic API key is not configured. Add one in Knowledgebase AI.")
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return "".join(block["text"] for block in data.get("content", []) if block.get("type") == "text")


async def _call_deepseek(
    prompt: str, system: str, max_tokens: int, temperature: float, timeout: int, provider=None
) -> str:
    api_key, model = _resolve_credentials(provider, "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL")
    if not api_key:
        raise AIUnavailableError("DeepSeek API key is not configured. Add one in Knowledgebase AI.")
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


_PROVIDER_CALLERS = {"claude": _call_anthropic, "deepseek": _call_deepseek}


async def generate_text(db, prompt: str, system: str) -> str:
    """Calls the configured default AI provider (falling back through
    provider_priority), respecting the admin's enabled/disabled toggle and
    per-call settings (timeout, max tokens, temperature) from AI
    Configuration. Each provider is retried up to config.retry_limit times
    on a transient HTTP failure before moving on to the next one in
    provider_priority."""
    config, providers = ai_config_service.get_configuration(db)
    if not config.is_enabled:
        raise AIUnavailableError(
            "AI features are currently disabled. An administrator can enable them in AI Configuration."
        )

    providers_by_id = {p.provider_id: p for p in providers}
    provider_order = config.provider_priority or [config.default_provider]
    errors: list[str] = []
    for provider_id in provider_order:
        caller = _PROVIDER_CALLERS.get(provider_id)
        if not caller:
            continue
        provider = providers_by_id.get(provider_id)
        attempts = max(1, config.retry_limit + 1)
        for attempt in range(attempts):
            try:
                return await caller(prompt, system, config.max_tokens, config.temperature, config.timeout_seconds, provider)
            except AIUnavailableError as exc:
                errors.append(str(exc))
                break  # not configured -- retrying won't help, try the next provider
            except httpx.HTTPStatusError as exc:
                errors.append(f"{provider_id}: provider returned {exc.response.status_code}")
                if attempt == attempts - 1:
                    break
            except httpx.HTTPError as exc:
                errors.append(f"{provider_id}: {exc}")
                if attempt == attempts - 1:
                    break

    raise AIUnavailableError(
        "; ".join(errors) if errors else "No AI provider is configured. Add an API key in Knowledgebase AI."
    )
