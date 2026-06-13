"""CRUD operations for voice conversation turns (the history tool's source)."""

from typing import List

from sqlalchemy.orm import Session

from src.models.voice_conversation import VoiceConversationTurn


def add_turn(
    db: Session,
    *,
    username: str,
    session_id: str,
    turn_index: int,
    user_text: str,
    bot_text: str,
) -> VoiceConversationTurn:
    """Insert one completed turn."""
    turn = VoiceConversationTurn(
        username=username,
        session_id=session_id,
        turn_index=turn_index,
        user_text=user_text,
        bot_text=bot_text,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def recent_turns_for_user(
    db: Session, username: str, limit: int = 50
) -> List[VoiceConversationTurn]:
    """Last ``limit`` turns for a user across all sessions, oldest-first.

    Powers the /chat transcript restore on refresh: fetches the newest rows by
    insertion order then reverses so the conversation reads chronologically.
    """
    rows = (
        db.query(VoiceConversationTurn)
        .filter(VoiceConversationTurn.username == username)
        .order_by(VoiceConversationTurn.id.desc())
        .limit(limit)
        .all()
    )
    return rows[::-1]


def recent_turns(db: Session, session_id: str, limit: int = 10) -> List[VoiceConversationTurn]:
    """Last ``limit`` turns of a session, oldest-first (chronological order).

    Fetches the newest rows then reverses so the model reads them in the order
    they happened — matching ``crud_slide_chat.get_recent_chat_messages``.
    """
    rows = (
        db.query(VoiceConversationTurn)
        .filter(VoiceConversationTurn.session_id == session_id)
        .order_by(VoiceConversationTurn.turn_index.desc(), VoiceConversationTurn.id.desc())
        .limit(limit)
        .all()
    )
    return rows[::-1]
