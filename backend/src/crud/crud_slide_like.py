"""CRUD operations for user_slide_like."""

from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.slide_like import UserSlideLike


def add_like(db: Session, username: str, quiz_id: int) -> None:
    """Insert a like row; idempotent on (username, quiz_id)."""
    db.execute(
        text(
            """
            INSERT INTO user_slide_like (username, quiz_id)
            VALUES (:username, :quiz_id)
            ON CONFLICT (username, quiz_id) DO NOTHING
            """
        ),
        {"username": username, "quiz_id": quiz_id},
    )
    db.commit()


def remove_like(db: Session, username: str, quiz_id: int) -> None:
    """Delete a like row; no-op if absent."""
    db.execute(
        text(
            """
            DELETE FROM user_slide_like
            WHERE username = :username AND quiz_id = :quiz_id
            """
        ),
        {"username": username, "quiz_id": quiz_id},
    )
    db.commit()


def is_liked(db: Session, username: str, quiz_id: int) -> bool:
    """Return True if the user has liked the quiz."""
    row = (
        db.query(UserSlideLike)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.quiz_id == quiz_id,
        )
        .first()
    )
    return row is not None


def get_liked_quiz_ids(db: Session, username: str) -> List[int]:
    """Return all quiz IDs the user has liked, newest first."""
    rows = (
        db.query(UserSlideLike.quiz_id)
        .filter(UserSlideLike.username == username)
        .order_by(UserSlideLike.liked_at.desc(), UserSlideLike.id.desc())
        .all()
    )
    return [row.quiz_id for row in rows]
