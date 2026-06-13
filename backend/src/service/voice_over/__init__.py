"""V2V Over Mode session proxy — press-to-talk Gemini Live over a WebSocket.

Each user turn runs inside its OWN fresh Live session (lazy open): the runner
waits for the browser's ``activity_start`` with no session held open, then opens
a session, replays the ``activity_start`` to Gemini, emits ``session_ready`` (the
browser's cue to arm the mic), runs the two pumps until the turn boundary, and
closes the session. Between turns no Gemini session exists, so the user's
reading/thinking time can never trip Gemini's idle deadline. History recall
survives the per-turn teardown because each completed turn is recorded to the DB
and read back via the ``get_conversation_history`` tool.
"""

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types

from src.service.voice_over.client import MODEL, get_client
from src.service.voice_over.config import _over_live_config
from src.service.voice_over.pumps import (
    _await_turn_start,
    _pump_browser_to_gemini,
    _pump_gemini_to_browser,
)

logger = logging.getLogger(__name__)


async def _run_one_turn(
    ws: WebSocket, *, username: str, voice: str, session_id: str, turn_index: int
) -> bool:
    """Run exactly one press-to-talk turn in its own fresh Live session.

    Returns ``ws_open`` — ``False`` when the WebSocket closed (while idle or
    mid-turn), the signal for the outer loop to stop.
    """
    if not await _await_turn_start(ws):
        return False
    client = get_client()
    config = _over_live_config(voice)
    logger.info("V2V-Over opening turn %d (voice=%s user=%s)", turn_index, voice, username)
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        # Replay the consumed activity_start so Gemini opens the turn, then tell
        # the browser it may arm the mic.
        await session.send_realtime_input(activity_start=types.ActivityStart())
        await ws.send_json({"type": "session_ready"})
        browser_task = asyncio.create_task(_pump_browser_to_gemini(ws, session))
        gemini_task = asyncio.create_task(
            _pump_gemini_to_browser(
                ws, session, username=username, session_id=session_id, turn_index=turn_index
            )
        )
        done, pending = await asyncio.wait(
            {browser_task, gemini_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            exc = task.exception()
            if exc is not None and not isinstance(exc, WebSocketDisconnect):
                raise exc
        if gemini_task in done:
            # Gemini reached a turn boundary (turn_complete / interrupted).
            return True
        # Browser pump finished first: True = barge-in (recycle); False = closed.
        return browser_task.exception() is None and bool(browser_task.result())


async def run_over_session(
    ws: WebSocket, *, username: str, voice: str, session_id: str, max_seconds: int
) -> None:
    """Run the per-turn loop until the WebSocket closes or the cap is hit."""

    async def _loop() -> None:
        turn_index = 0
        while True:
            ws_open = await _run_one_turn(
                ws, username=username, voice=voice, session_id=session_id, turn_index=turn_index
            )
            if not ws_open:
                return
            turn_index += 1

    try:
        await asyncio.wait_for(_loop(), timeout=max_seconds)
    except asyncio.TimeoutError:
        logger.info("V2V-Over session hit max_seconds=%d cap", max_seconds)
        try:
            await ws.send_json({"type": "end", "reason": "session_cap"})
        except Exception:  # pylint: disable=broad-except
            pass


__all__ = ["run_over_session", "MODEL", "get_client"]
