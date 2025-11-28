import textwrap
import re

#  Local imports
from config import constants


def ai_fpl_helper(prompt, SYSTEM_PROMPT, client_free, client_paid, API_KEY):
    """
    Get AI recommendations for FPL transfers.
    Args:
        prompt: json of players with replacements
        SYSTEM_PROMPT: system prompt for AI model
        client_free: OpenAI client for free API usage
        client_paid: OpenAI client for paid API usage
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
        # Try with free key first
        if client_free:
            resp = client_free.chat.completions.create(
                model=constants.AI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
        elif client_paid:
            print("💳 Using paid key (no free key configured)")
            resp = client_paid.chat.completions.create(
                model=constants.AI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
        else:
            return "AI Error: No available client."
    except Exception as e:
        err_msg = str(e).lower()
        retry_errors = [
            "request too large",
            "rate_limit_exceeded",
            "need more tokens",
            "limit",
            "tpm",
            "rpm",
        ]
        if any(word in err_msg for word in retry_errors) and client_paid:
            print("\n")
            print("Free-tier limit hit — retrying with paid key...")
            resp = client_paid.chat.completions.create(
                model=constants.AI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
        else:
            return f"AI Error: {e}\nDo you have VPN on..."
    raw = resp.choices[0].message.content.strip()
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    wrapped = "\n".join(textwrap.fill(line, width=120) for line in cleaned.splitlines())
    return wrapped
