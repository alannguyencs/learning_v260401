"""Runtime streaming pumps for V2V Over Mode.

``_pump_browser_to_gemini`` translates the browser's manual-turn control frames
(``activity_start`` / ``activity_end`` / ``interrupt``) and mic audio into Gemini
realtime input; ``_pump_gemini_to_browser`` fans Gemini events back out (audio,
transcripts, control frames) and answers tool calls. ``_await_turn_start`` is the
lazy-open gate — no Live session is opened until the user presses to start a
turn, so the model session is never held idle across the user's reaction time
(which trips Gemini's deadline).
"""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types

from src.service.voice_over.emit import (
    _emit_control_events,
    _emit_parts,
    _peak_int16,
    _record_live_turn,
)
from src.service.voice_over.tools import handle_tool_call

logger = logging.getLogger(__name__)

# Int16 PCM peak below this is treated as effectively silent.
_SILENCE_PEAK_THRESHOLD = 500


async def _await_turn_start(ws: WebSocket) -> bool:
    """Block until the browser sends the next ``activity_start`` frame.

    Returns ``True`` once it arrives (caller opens a fresh Live session), or
    ``False`` if the WebSocket closes first (stop the per-turn loop). Stray
    binary or other control frames while idle are dropped.
    """
    try:
        while True:
            message = await ws.receive()
            if message.get("type") == "websocket.disconnect":
                return False
            text = message.get("text")
            if text is None:
                continue
            try:
                control = json.loads(text)
            except (ValueError, TypeError):
                continue
            if isinstance(control, dict) and control.get("type") == "activity_start":
                return True
    except WebSocketDisconnect:
        return False


async def _pump_gemini_to_browser(
    ws: WebSocket, session, *, username: str, session_id: str, turn_index: int
) -> None:
    """Fan out one turn of Gemini events; return at the turn boundary.

    Answers tool calls via ``handle_tool_call``. On ``turn_complete`` records the
    turn to history. Returns the moment a ``turn_complete`` or ``interrupted`` is
    seen so the per-turn runner can tear the session down and open a fresh one.
    """
    turn_input: list = []
    turn_output: list = []
    async for msg in session.receive():
        tool_call = getattr(msg, "tool_call", None)
        if tool_call is not None and getattr(tool_call, "function_calls", None):
            names = [getattr(fc, "name", None) for fc in tool_call.function_calls]
            logger.info("V2V-Over tool_call: %s", names)
            await handle_tool_call(session, tool_call, username=username)
            continue
        sc = getattr(msg, "server_content", None)
        if sc is None:
            continue
        in_tr = getattr(sc, "input_transcription", None)
        if in_tr is not None and getattr(in_tr, "text", None):
            turn_input.append(in_tr.text)
        out_tr = getattr(sc, "output_transcription", None)
        if out_tr is not None and getattr(out_tr, "text", None):
            turn_output.append(out_tr.text)
        await _emit_parts(ws, sc)
        if getattr(sc, "turn_complete", False):
            _record_live_turn(username, session_id, turn_index, turn_input, turn_output)
            turn_input, turn_output = [], []
        await _emit_control_events(ws, sc)
        if getattr(sc, "turn_complete", False) or getattr(sc, "interrupted", False):
            return


def _parse_control(text):
    """Parse a text control frame into a dict, or None if absent/malformed."""
    if text is None:
        return None
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


async def _send_audio(session, data: bytes) -> None:
    """Forward one mic PCM frame to Gemini realtime input."""
    await session.send_realtime_input(
        audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000"),
    )


async def _forward_control(control, session, turn_peak: int) -> str:
    """Translate one browser control frame into Gemini realtime input.

    Returns a signal: ``"start"`` (turn opened, reset peak), ``"interrupt"``
    (barge-in — stop the pump), or ``""`` (handled, keep going).
    """
    kind = control.get("type") if isinstance(control, dict) else None
    if kind == "activity_start":
        await session.send_realtime_input(activity_start=types.ActivityStart())
        return "start"
    if kind == "activity_end":
        if turn_peak < _SILENCE_PEAK_THRESHOLD:
            logger.warning("V2V-Over turn likely silent (peak=%d)", turn_peak)
        await session.send_realtime_input(activity_end=types.ActivityEnd())
        return ""
    if kind == "interrupt":
        logger.info("V2V-Over barge-in (interrupt)")
        return "interrupt"
    logger.warning("V2V-Over ignoring control frame: %r", kind)
    return ""


async def _pump_browser_to_gemini(ws: WebSocket, session) -> bool:
    """Forward browser frames to Gemini, translating manual-turn control frames.

    Binary frames are 16 kHz Int16 mono PCM. Control frames (handled in
    ``_forward_control``): ``activity_start`` opens a turn, ``activity_end``
    closes it and asks Gemini to reply, ``interrupt`` aborts the in-progress
    reply (barge-in).

    Returns ``True`` when it stopped on an ``interrupt`` (recycle the session),
    or ``False`` when the WebSocket closed (stop the per-turn loop).
    """
    turn_peak = 0
    try:
        while True:
            message = await ws.receive()
            if message.get("type") == "websocket.disconnect":
                return False
            data = message.get("bytes")
            if data is not None:
                turn_peak = max(turn_peak, _peak_int16(data))
                await _send_audio(session, data)
                continue
            control = _parse_control(message.get("text"))
            if control is None:
                continue
            signal = await _forward_control(control, session, turn_peak)
            if signal == "interrupt":
                return True
            if signal == "start":
                turn_peak = 0
    except WebSocketDisconnect:
        return False
