import json
import os

import anthropic

_claude  = None
_openai  = None


def _get_claude():
    global _claude
    if _claude is None:
        _claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=25.0)
    return _claude


def _get_openai():
    global _openai
    if _openai is None:
        from openai import OpenAI
        _openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai


def _parse(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def _call_claude(system_prompt, user_message, model, max_tokens):
    client = _get_claude()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_message}],
    )
    return _parse(response.content[0].text)


def _call_openai(system_prompt, user_message, max_tokens):
    client = _get_openai()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    return _parse(response.choices[0].message.content)


def call(system_prompt: str, user_message: str, model: str, max_tokens: int) -> dict:
    from .moderation import check as mod_check, ModerationError
    try:
        mod_check(user_message)
    except ModerationError:
        raise RuntimeError(
            "Your request could not be processed. If you believe this is a mistake, "
            "contact pedro_torres@torrestechremote.com."
        ) from None

    try:
        return _call_claude(system_prompt, user_message, model, max_tokens)
    except anthropic.AuthenticationError:
        pass
    except anthropic.APIStatusError as e:
        if e.status_code in (401, 403):
            pass
        else:
            msg = (e.body or {}).get("error", {}).get("message") or str(e)
            raise RuntimeError(msg) from None
    except anthropic.APIConnectionError:
        pass

    # Claude unavailable — try OpenAI GPT-4.1 mini
    try:
        return _call_openai(system_prompt, user_message, max_tokens)
    except KeyError:
        raise RuntimeError(
            "AI service is temporarily unavailable and no fallback key is configured."
        ) from None
    except Exception as e:
        raise RuntimeError(f"All AI providers failed: {e}") from None
