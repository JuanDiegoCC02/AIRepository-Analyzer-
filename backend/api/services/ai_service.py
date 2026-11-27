import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """
    The AI provider could not produce an answer.

    The message is safe to log: it never contains the API key, the prompt
    or the text returned by the provider.
    """


def read_bool_setting(name, default=False):
    """Read a boolean setting that may also come as text ("true", "1")."""
    value = getattr(settings, name, default)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")

    return default


def read_int_setting(name, default, minimum, maximum):
    """Read an integer setting limited to [minimum, maximum]."""
    value = getattr(settings, name, default)

    if isinstance(value, bool):
        return default

    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    return max(minimum, min(number, maximum))


class AIClient:
    """
    Minimal client for the Anthropic Messages API.

    It uses `requests` (already a dependency), so no new package is needed.
    Safety rules:
      - the URL is a constant: nothing from GitHub or the user can change
        where the request goes;
      - the API key only comes from the environment (settings) and is
        sent only in a header; it is never logged or put in an exception;
      - there is a timeout, no redirects and no retries, so a slow
        provider can delay an analysis by at most AI_TIMEOUT_SECONDS.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    DEFAULT_MODEL = "claude-haiku-5-5"
    MODEL_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")

    @classmethod
    def api_key(cls):
        value = getattr(settings, "ANTHROPIC_API_KEY", None)

        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

    @classmethod
    def model(cls):
        value = getattr(settings, "AI_MODEL", None)

        if isinstance(value, str) and cls.MODEL_PATTERN.fullmatch(value):
            return value

        return cls.DEFAULT_MODEL

    @classmethod
    def timeout(cls):
        return read_int_setting("AI_TIMEOUT_SECONDS", 20, 1, 60)

    @classmethod
    def max_tokens(cls):
        return read_int_setting("AI_MAX_TOKENS", 500, 50, 2000)

    @classmethod
    def is_enabled(cls):
        """True only when AI is switched on AND an API key exists."""
        return read_bool_setting("AI_SUMMARY_ENABLED") and bool(cls.api_key())

    @classmethod
    def complete(cls, system, user_message):
        """
        Send one request and return {"text": str, "truncated": bool}.

        Raises AIServiceError for any failure.
        """
        key = cls.api_key()

        if not key:
            raise AIServiceError("No API key is configured.")

        payload = {
            "model": cls.model(),
            "max_tokens": cls.max_tokens(),
            "system": system,
            "messages": [{"role": "user", "content": user_message}],
        }
        headers = {
            "x-api-key": key,
            "anthropic-version": cls.API_VERSION,
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                cls.API_URL,
                json=payload,
                headers=headers,
                timeout=cls.timeout(),
                allow_redirects=False,
            )
        except requests.Timeout:
            raise AIServiceError("The AI provider timed out.") from None
        except requests.RequestException:
            raise AIServiceError("The AI provider is unreachable.") from None

        if response.status_code != 200:
            raise AIServiceError(
                f"The AI provider answered with status {response.status_code}."
            )

        try:
            data = response.json()
            blocks = data["content"]

            if not isinstance(blocks, list):
                raise TypeError("content must be a list")

            text = "".join(
                block["text"]
                for block in blocks
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            )
            stop_reason = data.get("stop_reason")
        except (ValueError, KeyError, TypeError, AttributeError):
            raise AIServiceError(
                "The AI provider returned an unexpected response."
            ) from None

        return {
            "text": text,
            "truncated": stop_reason == "max_tokens",
        }
