"""WS /api/voice/v2v-over — press-to-talk Voice → Voice sessions.

Bidirectional Gemini Live session over a WebSocket (binary PCM + JSON control
events). Closes 4401 (before accept) when the auth cookie is missing/invalid,
4001 when ``?voice=`` is unknown. A hard session cap is enforced in the runner.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request, get_current_user_from_token
from src.configs import settings
from src.crud import crud_voice_conversation
from src.database import SessionLocal, get_db
from src.service import voice_over as voice_over_service
from src.service.voice_over.client import DEFAULT_VOICE, VOICE_NAMES

router = APIRouter()
logger = logging.getLogger(__name__)


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/voice/history")
def voice_history(
    limit: int = Query(50, ge=1, le=200),
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Recent conversation turns for the user, flattened to chat bubbles.

    Each stored turn becomes a user bubble followed by an assistant bubble, in
    chronological order, so /chat can restore the transcript on refresh.
    """
    turns = crud_voice_conversation.recent_turns_for_user(db, user.username, limit)
    bubbles = []
    for turn in turns:
        if turn.user_text and turn.user_text.strip():
            bubbles.append({"role": "user", "text": turn.user_text})
        if turn.bot_text and turn.bot_text.strip():
            bubbles.append({"role": "assistant", "text": turn.bot_text})
    return {"turns": bubbles}


def _authenticate(ws: WebSocket):
    """Return the user for the WS auth cookie, or None."""
    token = ws.cookies.get("access_token")
    if not token:
        return None
    db = SessionLocal()
    try:
        return get_current_user_from_token(db, token)
    finally:
        db.close()


@router.websocket("/voice/v2v-over")
async def ws_v2v_over(ws: WebSocket, voice: str = DEFAULT_VOICE) -> None:
    """Press-to-talk Voice → Voice over a Gemini Live session."""
    user = _authenticate(ws)
    if user is None:
        await ws.close(code=4401, reason="not authenticated")
        return
    if voice not in VOICE_NAMES:
        await ws.close(code=4001, reason=f"invalid voice: {voice}")
        return
    await ws.accept()
    session_id = uuid.uuid4().hex
    logger.info("V2V-Over session %s opened for %s", session_id, user.username)
    try:
        await voice_over_service.run_over_session(
            ws,
            username=user.username,
            voice=voice,
            session_id=session_id,
            max_seconds=settings.voice_session_max_seconds,
        )
    except WebSocketDisconnect:
        logger.info("V2V-Over client disconnected (%s)", session_id)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("V2V-Over session %s failed", session_id)
        try:
            await ws.send_json(
                {"type": "error", "detail": f"{exc.__class__.__name__}: {str(exc)[:400]}"}
            )
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            await ws.close(code=1011)
        except Exception:  # pylint: disable=broad-except
            pass
