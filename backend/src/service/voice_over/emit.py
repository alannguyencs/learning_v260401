"""Output helpers for V2V Over Mode: emit Gemini events + record turns.

``_emit_parts`` sends model audio as binary frames and any text parts as
transcript control events; ``_emit_control_events`` forwards transcripts and
turn-boundary signals; ``_record_live_turn`` persists one completed turn to the
voice conversation history (the source for the get_conversation_history tool).
"""

import array
import logging
import sys

from fastapi import WebSocket

from src.crud import crud_voice_conversation
from src.database import SessionLocal
from src.utils.pcm import coerce_pcm

logger = logging.getLogger(__name__)


def _peak_int16(frame: bytes) -> int:
    """Absolute peak of an Int16 little-endian PCM frame (0..32767)."""
    even_len = len(frame) & ~1
    if even_len == 0:
        return 0
    samples = array.array("h")
    samples.frombytes(frame[:even_len])
    if sys.byteorder != "little":
        samples.byteswap()
    peak = 0
    for s in samples[::16]:  # sample every 16th for cheap stats
        peak = max(peak, -s if s < 0 else s)
    return peak


async def _emit_parts(ws: WebSocket, sc) -> None:
    """Send audio bytes as binary frames; text parts as output transcripts."""
    model_turn = getattr(sc, "model_turn", None)
    if model_turn is None:
        return
    for part in getattr(model_turn, "parts", None) or []:
        inline = getattr(part, "inline_data", None)
        if inline is not None and getattr(inline, "data", None):
            await ws.send_bytes(coerce_pcm(inline.data))
        text = getattr(part, "text", None)
        if text:
            await ws.send_json({"type": "output_transcript", "text": text})


async def _emit_control_events(ws: WebSocket, sc) -> None:
    """Forward transcripts + interrupt / turn_complete control frames."""
    input_tr = getattr(sc, "input_transcription", None)
    if input_tr is not None and getattr(input_tr, "text", None):
        await ws.send_json({"type": "input_transcript", "text": input_tr.text})
    output_tr = getattr(sc, "output_transcription", None)
    if output_tr is not None and getattr(output_tr, "text", None):
        await ws.send_json({"type": "output_transcript", "text": output_tr.text})
    if getattr(sc, "interrupted", False):
        await ws.send_json({"type": "interrupted"})
    if getattr(sc, "turn_complete", False):
        await ws.send_json({"type": "turn_complete"})


def _record_live_turn(
    username: str,
    session_id: str,
    turn_index: int,
    input_parts: list,
    output_parts: list,
) -> None:
    """Persist one completed turn (best-effort; empty turns are skipped)."""
    user_input = "".join(input_parts).strip()
    bot_output = "".join(output_parts).strip()
    if not user_input and not bot_output:
        return
    db = SessionLocal()
    try:
        crud_voice_conversation.add_turn(
            db,
            username=username,
            session_id=session_id,
            turn_index=turn_index,
            user_text=user_input or "[no transcript]",
            bot_text=bot_output or "[no transcript]",
        )
    except Exception:  # pylint: disable=broad-except
        logger.exception("V2V-Over failed to record turn %d", turn_index)
    finally:
        db.close()
