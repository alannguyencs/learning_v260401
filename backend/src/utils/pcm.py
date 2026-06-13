"""PCM byte helpers for the Gemini Live audio path.

google-genai returns ``inline_data.data`` as raw PCM under a plain interpreter
but as ASCII-encoded base64 text under uvicorn — both shapes reach the same
call site, so this helper sniffs and decodes the base64 case. The branch fires
under uvicorn; do not remove it as dead code.
"""

import base64

# Bytes that can appear in standard + url-safe base64 output (incl. padding).
_BASE64_BYTES = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/-_=")


def coerce_pcm(raw: bytes) -> bytes:
    """Return raw PCM bytes, decoding from ASCII-base64 if needed."""
    if not raw:
        return raw
    sample = raw[:256]
    if all(b in _BASE64_BYTES for b in sample):
        try:
            return base64.b64decode(raw, validate=False)
        except (ValueError, base64.binascii.Error):
            return raw
    return raw
