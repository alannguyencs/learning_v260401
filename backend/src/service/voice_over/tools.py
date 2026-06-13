"""Function-tool handling for V2V Over Mode.

Answers the model's ``search_notes`` and ``get_conversation_history`` function
calls and replies via ``send_tool_response`` — the channel the native-audio
model honors. Both backing reads are synchronous (BM25 over Postgres rows / a DB
read), so they run in the default thread-pool executor and are bounded by a hard
budget: the native-audio model pauses generation until the tool response
arrives, and Gemini reaps the whole turn if it overruns its deadline, so a slow
read returns an empty result rather than stalling the turn.
"""

import asyncio
import logging

from google.genai import types

from src.crud import crud_voice_conversation
from src.database import SessionLocal
from src.service.notes_search import search_notes

logger = logging.getLogger(__name__)

# Bound each tool call so a slow read cannot trip Gemini's turn deadline.
_TOOL_RESPONSE_BUDGET_SECONDS = 4.0
# Cap history handed to the model (oldest-first), bounding tool-response size.
_HISTORY_EXCHANGE_CAP = 6
_NOTES_TOP_K = 3
# Relevance cutoff for note hits. BM25 returns the top-k by keyword overlap, but
# some are off-topic (e.g. an MCP note surfacing on a "full-stack web app" query).
# Drop hits with negligible overlap, and any hit far weaker than the best match,
# so only notes clearly about the user's topic reach the model.
_NOTES_MIN_SCORE = 0.1
_NOTES_REL_RATIO = 0.5


def _relevant_hits(hits: list) -> list:
    """Keep only on-topic note hits (``hits`` are BM25 score-descending)."""
    strong = [h for h in hits if h.score >= _NOTES_MIN_SCORE]
    if not strong:
        return []
    cutoff = strong[0].score * _NOTES_REL_RATIO
    return [h for h in strong if h.score >= cutoff]


def _notes_for_tool(query: str) -> dict:
    """BM25-search the notes corpus for the get-notes tool (sync)."""
    db = SessionLocal()
    try:
        raw = search_notes(db, query, top_k=_NOTES_TOP_K)
    finally:
        db.close()
    hits = _relevant_hits(raw)
    if len(hits) != len(raw):
        logger.info(
            "V2V-Over notes filter: %d → %d hit(s) after relevance cutoff", len(raw), len(hits)
        )
    return {
        "notes": [{"title": h.title, "rel_path": h.rel_path, "content": h.content} for h in hits]
    }


def _history_for_tool(username: str) -> dict:
    """Read the user's recent turns for the history tool (sync).

    Scoped by username across all sessions (not the current session_id) so the
    model recalls earlier conversations after a page refresh, which mints a new
    session each time.
    """
    if not username:
        return {"history": []}
    db = SessionLocal()
    try:
        rows = crud_voice_conversation.recent_turns_for_user(
            db, username, limit=_HISTORY_EXCHANGE_CAP
        )
    finally:
        db.close()
    return {"history": [{"user": r.user_text, "assistant": r.bot_text} for r in rows]}


async def _run_bounded(func, *args) -> dict:
    """Run ``func(*args)`` in the executor under the tool-response budget."""
    loop = asyncio.get_event_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, func, *args),
            timeout=_TOOL_RESPONSE_BUDGET_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "V2V-Over tool exceeded %.1fs budget — empty result", _TOOL_RESPONSE_BUDGET_SECONDS
        )
        return {}
    except Exception:  # pylint: disable=broad-except
        # CancelledError is a BaseException, so it propagates past this handler.
        logger.exception("V2V-Over tool failed — empty result")
        return {}


async def handle_tool_call(session, tool_call, *, username: str) -> None:
    """Answer the model's function calls via ``send_tool_response``."""
    responses = []
    for fc in getattr(tool_call, "function_calls", None) or []:
        name = getattr(fc, "name", None) or ""
        args = dict(getattr(fc, "args", None) or {})
        if name == "search_notes":
            query = (args.get("query") or "").strip()
            payload = await _run_bounded(_notes_for_tool, query) if query else {"notes": []}
            logger.info(
                "V2V-Over search_notes: query=%r → %d note(s)",
                query[:80],
                len(payload.get("notes", [])),
            )
        elif name == "get_conversation_history":
            payload = await _run_bounded(_history_for_tool, username)
            logger.info("V2V-Over history: %d exchange(s)", len(payload.get("history", [])))
        else:
            logger.warning("V2V-Over ignoring unknown tool %r", name)
            payload = {}
        responses.append(
            types.FunctionResponse(
                id=getattr(fc, "id", None),
                name=name or "search_notes",
                response=payload,
            )
        )
    if responses:
        await session.send_tool_response(function_responses=responses)
