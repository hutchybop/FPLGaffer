import textwrap
import re

#  Local imports
from config import constants


def _extract_responses_text(resp):
    """Extract text output from OpenAI Responses API result."""
    output_text = getattr(resp, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    outputs = getattr(resp, "output", None) or []
    chunks = []
    for item in outputs:
        for content in getattr(item, "content", []) or []:
            text_value = getattr(content, "text", None)
            if isinstance(text_value, str) and text_value.strip():
                chunks.append(text_value)
    return "\n".join(chunks).strip()


def ai_fpl_helper(prompt, SYSTEM_PROMPT, client, API_KEY):
    """
    Get AI recommendations for FPL transfers.
    Args:
        prompt: json of players with replacements
        SYSTEM_PROMPT: system prompt for AI model
        client: OpenAI client instance
        API_KEY: boolean indicating if API key is available
    Returns:
        str: formatted AI response text
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    # No keys configured
    if not API_KEY:
        return "AI features disabled — No API key found in .env."
    try:
        if not client:
            return "AI Error: No available client."

        raw = ""
        model_name = (constants.AI_MODEL or "").lower()

        # Zen GPT models are served via /responses endpoint.
        if model_name.startswith("gpt-"):
            try:
                resp = client.responses.create(
                    model=constants.AI_MODEL,
                    input=messages,
                    temperature=0.3,
                    max_output_tokens=600,
                )
                raw = _extract_responses_text(resp)
            except Exception:
                raw = ""

        if not raw:
            resp = client.chat.completions.create(
                model=constants.AI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            raw = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"AI Error: {e}\nDo you have VPN on..."

    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Preserve strict JSON-like outputs (used by wildcard validation).
    if cleaned.startswith("{") or cleaned.startswith("["):
        return cleaned

    wrapped = "\n".join(textwrap.fill(line, width=120) for line in cleaned.splitlines())
    return wrapped
