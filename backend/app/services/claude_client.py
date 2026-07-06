import base64
import json
import os

import anthropic

_claude  = None
_openai  = None

# Anthropic's supported vision media types. Every image we send has already
# been normalized to JPEG by file_handler.prepare_image, but this list is kept
# as a real check (not decoration) in case a future caller passes something else.
IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGES = 6

# Human-readable names for the instruction we inject into the system prompt.
# Keep in sync with the frontend's supportedLngs and app/routes/profile.py.
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "ru": "Russian",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "sv": "Swedish",
    "uk": "Ukrainian",
    "el": "Greek",
    "he": "Hebrew",
    "cs": "Czech",
    "ro": "Romanian",
}


def _with_language_instruction(system_prompt: str, language: str) -> str:
    # English is the model's default — nothing to add. Anything else gets an
    # explicit instruction appended so the tool output itself (not just the
    # UI chrome) comes back in the user's chosen language.
    if not language or language == "en":
        return system_prompt
    lang_name = LANGUAGE_NAMES.get(language, language)
    return (
        f"{system_prompt}\n\n"
        f"IMPORTANT: Write all natural-language content in your response in {lang_name}. "
        f"Keep JSON keys exactly as specified in English — only the string values should be in {lang_name}."
    )


def to_image_content(jpeg_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Wrap already-normalized image bytes into the shape `call(images=...)` expects."""
    return {"media_type": media_type, "data": base64.b64encode(jpeg_bytes).decode()}


def _build_content(user_message: str, images: list | None):
    # No images: keep the exact original shape (a plain string) so every
    # existing text-only call site behaves byte-for-byte the same as before.
    if not images:
        return user_message

    if len(images) > MAX_IMAGES:
        raise ValueError(f"Too many photos — {MAX_IMAGES} max per submission.")

    content = []
    if user_message:
        content.append({"type": "text", "text": user_message})
    for image in images:
        media_type = image["media_type"]
        if media_type not in IMAGE_MEDIA_TYPES:
            raise ValueError(f"Unsupported image type '{media_type}'.")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image["data"]},
        })
    return content


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


def _call_claude(system_prompt, content, model, max_tokens):
    client = _get_claude()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
    )
    return _parse(response.content[0].text)


def _call_openai(system_prompt, content, max_tokens):
    client = _get_openai()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": content},
        ],
    )
    return _parse(response.choices[0].message.content)


def call(system_prompt: str, user_message: str, model: str, max_tokens: int, language: str = "en", images: list | None = None) -> dict:
    from .moderation import check as mod_check, ModerationError
    try:
        mod_check(user_message)
    except ModerationError:
        raise RuntimeError(
            "Your request could not be processed. If you believe this is a mistake, "
            "contact pedro_torres@torrestechremote.com."
        ) from None

    system_prompt = _with_language_instruction(system_prompt, language)
    content = _build_content(user_message, images)

    try:
        return _call_claude(system_prompt, content, model, max_tokens)
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

    if images:
        # The OpenAI fallback below only knows how to send plain text — its vision
        # format is shaped differently from Anthropic's and isn't implemented here.
        # Rather than guess at a second image format, surface a clear error so the
        # user knows to retry shortly or fall back to a text/document upload.
        raise RuntimeError(
            "Photo analysis is temporarily unavailable. Please try again shortly, "
            "or use a text/document upload instead."
        )

    # Claude unavailable — try OpenAI GPT-4.1 mini
    try:
        return _call_openai(system_prompt, content, max_tokens)
    except KeyError:
        raise RuntimeError(
            "AI service is temporarily unavailable and no fallback key is configured."
        ) from None
    except Exception as e:
        raise RuntimeError(f"All AI providers failed: {e}") from None
