"""Gemini Live client + model id + voice catalog for V2V Over Mode.

The client is a lazily-built singleton; a missing GEMINI_API_KEY does not raise
here — the constructed client raises at call time.
"""

from google import genai

from src.configs import settings

MODEL = settings.voice_live_model

# Gemini Live prebuilt voices. ``?voice=`` must be one of these.
VOICE_NAMES = frozenset(
    {
        "Aoede",
        "Charon",
        "Fenrir",
        "Kore",
        "Leda",
        "Orus",
        "Puck",
        "Zephyr",
    }
)
DEFAULT_VOICE = settings.voice_default_name

_client: "genai.Client | None" = None


def get_client() -> "genai.Client":
    """Return this package's lazily-constructed singleton Gemini client."""
    global _client  # pylint: disable=global-statement
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client
