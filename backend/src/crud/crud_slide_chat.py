"""CRUD operations for slide chat messages."""

from typing import List

from sqlalchemy.orm import Session

from src.models.slide_chat import SlideChatMessage


def get_chat_messages(db: Session, username: str, slide_identifier: str) -> List[SlideChatMessage]:
    """All messages for a user+slide, ordered by created_at ASC."""
    return (
        db.query(SlideChatMessage)
        .filter(
            SlideChatMessage.username == username,
            SlideChatMessage.slide_identifier == slide_identifier,
        )
        .order_by(SlideChatMessage.created_at.asc(), SlideChatMessage.id.asc())
        .all()
    )


def get_recent_chat_messages(
    db: Session, username: str, slide_identifier: str, limit: int = 10
) -> List[SlideChatMessage]:
    """Last N messages for context window."""
    return (
        db.query(SlideChatMessage)
        .filter(
            SlideChatMessage.username == username,
            SlideChatMessage.slide_identifier == slide_identifier,
        )
        .order_by(SlideChatMessage.created_at.desc(), SlideChatMessage.id.desc())
        .limit(limit)
        .all()
    )[::-1]


def save_chat_message(
    db: Session, username: str, slide_identifier: str, role: str, content: str
) -> SlideChatMessage:
    """Insert one message row."""
    msg = SlideChatMessage(
        username=username,
        slide_identifier=slide_identifier,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
