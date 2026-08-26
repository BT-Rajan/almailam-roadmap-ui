"""Real LLM integration layer.

Every AI feature in this app -- the knowledgebase Q&A tool and the New
Client wizard's identification-document plausibility check -- goes through
generate_text() (or the vision variant) below, which calls a real
provider's API using a real API key from environment variables (see
app.core.config.Settings) -- never a fabricated response. If no key is
configured, or AI is disabled in AI Configuration, this raises
AIUnavailableError, and every caller in this module turns that into a
clear "not available" result rather than making something up.

Two providers are supported, matching AI_PROVIDER_IDS in
app.models.ai_config: Anthropic (Claude) and DeepSeek.
"""

import json

import httpx

from app.core.config import get_settings
from app.services import ai_config_service


class AIUnavailableError(Exception):
    """Raised when AI features are disabled, unconfigured, or a live call
    fails -- callers must turn this into an honest 'unavailable' response,
    never fall back to fabricated content."""


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


async def _call_anthropic(prompt: str, system: str, max_tokens: int, temperature: float, timeout: int) -> str:
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise AIUnavailableError("Anthropic API key is not configured on the server.")
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return "".join(block["text"] for block in data.get("content", []) if block.get("type") == "text")


async def _call_deepseek(prompt: str, system: str, max_tokens: int, temperature: float, timeout: int) -> str:
    settings = get_settings()
    if not settings.DEEPSEEK_API_KEY:
        raise AIUnavailableError("DeepSeek API key is not configured on the server.")
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}", "content-type": "application/json"},
            json={
                "model": settings.DEEPSEEK_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic_vision(
    image_base64: str, media_type: str, prompt: str, system: str, max_tokens: int, temperature: float, timeout: int
) -> str:
    """Same request shape as _call_anthropic, but attaches an image to
    the message -- used only by verify_identification_document below.
    Claude is the only configured provider with vision support here;
    DeepSeek's chat API doesn't take image input, so this is never
    routed through _PROVIDER_CALLERS the way text calls are. Callers
    needing vision call this directly and must treat a provider that
    isn't Claude (or isn't configured at all) as AI being unavailable
    for this specific check, not as an error to surface."""
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        # This is the expected, common case for a DeepSeek-only setup,
        # not a misconfiguration -- DeepSeek's public API is text-only
        # (confirmed against their current documentation), so any
        # vision check always needs Claude specifically, regardless of
        # which provider is set as the default for text features.
        raise AIUnavailableError(
            "Document image verification requires an Anthropic (Claude) API key -- DeepSeek's "
            "API doesn't support image input. Configure an Anthropic key to enable this check; "
            "without one, documents are accepted with a manual-verification caveat instead."
        )
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_base64}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        return "".join(block["text"] for block in data.get("content", []) if block.get("type") == "text")


_PROVIDER_CALLERS = {"claude": _call_anthropic, "deepseek": _call_deepseek}


async def generate_text(db, prompt: str, system: str) -> str:
    """Calls the configured default AI provider (falling back through
    provider_priority), respecting the admin's enabled/disabled toggle and
    per-call settings (timeout, max tokens, temperature) from AI
    Configuration. Each provider is retried up to config.retry_limit times
    on a transient HTTP failure before moving on to the next one in
    provider_priority."""
    config, _providers = ai_config_service.get_configuration(db)
    if not config.is_enabled:
        raise AIUnavailableError(
            "AI features are currently disabled. An administrator can enable them in AI Configuration."
        )

    provider_order = config.provider_priority or [config.default_provider]
    errors: list[str] = []
    for provider_id in provider_order:
        caller = _PROVIDER_CALLERS.get(provider_id)
        if not caller:
            continue
        attempts = max(1, config.retry_limit + 1)
        for attempt in range(attempts):
            try:
                return await caller(prompt, system, config.max_tokens, config.temperature, config.timeout_seconds)
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
        "; ".join(errors) if errors else "No AI provider is configured. Add an API key in AI Configuration."
    )


IDENTIFICATION_CHECK_SYSTEM_PROMPT = (
    "You are a document classification assistant for an engineering consulting firm's client "
    "onboarding process. You are shown an image a staff member has uploaded as a specific type of "
    "identification document. Determine only whether the image plausibly shows that type of "
    "document (not whether it is genuine, unexpired, or otherwise valid -- that's a human "
    "verification step later in the process). Always respond with only a single valid JSON object, "
    "no other text, no markdown fences."
)


def _identification_check_prompt(document_type: str) -> str:
    return f"""The staff member selected "{document_type}" as the document type for this upload.

Does this image plausibly show a {document_type} (front or back), as opposed to some other kind of
document or an unrelated image entirely? Judge only the general visual category of document -- do
not attempt to read or verify any specific details, numbers, or names on it.

Respond with exactly this JSON shape:
{{
  "matches": true | false,
  "reasoning": "one short sentence explaining the judgment"
}}"""


async def verify_identification_document(db, image_base64: str, media_type: str, document_type: str) -> dict:
    """Vision check for the New Client wizard's identification upload:
    does the image plausibly show the document type the staff member
    selected? Only ever called for image files (jpg/jpeg/png) -- PDFs
    and any AI failure are the caller's responsibility to treat as
    "couldn't check, accept with a manual-verification caveat" rather
    than calling this at all, since this function's only two outcomes
    are a real result or AIUnavailableError, never a fabricated guess.

    This is a lightweight plausibility check, not a substitute for the
    app's existing verification workflow (ClientVerification records) --
    it catches an obviously wrong upload (a selfie, a random photo, a
    different document type) at the moment of upload, not whether a
    genuine Civil ID is itself authentic or unexpired.
    """
    config, _providers = ai_config_service.get_configuration(db)
    if not config.is_enabled:
        raise AIUnavailableError("AI features are currently disabled.")

    try:
        text = await _call_anthropic_vision(
            image_base64,
            media_type,
            _identification_check_prompt(document_type),
            IDENTIFICATION_CHECK_SYSTEM_PROMPT,
            config.max_tokens,
            config.temperature,
            config.timeout_seconds,
        )
    except httpx.HTTPStatusError as exc:
        raise AIUnavailableError(f"AI provider returned {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise AIUnavailableError(f"AI provider request failed: {exc}") from exc
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIUnavailableError("The AI provider's response could not be understood.") from exc

    return {
        "matches": bool(result.get("matches", False)),
        "reasoning": str(result.get("reasoning", ""))[:500],
    }
