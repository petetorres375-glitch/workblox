import json
import os

import anthropic

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def call(system_prompt: str, user_message: str, model: str, max_tokens: int) -> dict:
    import anthropic as _anthropic

    client = get_client()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
    except _anthropic.APIStatusError as e:
        msg = (e.body or {}).get("error", {}).get("message") or str(e)
        raise RuntimeError(msg) from None
    except _anthropic.APIConnectionError as e:
        raise RuntimeError("Could not reach the AI service. Check your connection.") from None

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)
