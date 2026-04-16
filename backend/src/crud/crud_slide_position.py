"""CRUD operations for slide navigation: UserSlidePosition, SlideHistory."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.slide_position import SlideHistory, UserSlidePosition


def get_position(db: Session, username: str) -> Optional[UserSlidePosition]:
    """Fetch the current slide position for the user."""
    return db.query(UserSlidePosition).filter(UserSlidePosition.username == username).first()


def save_position(
    db: Session,
    username: str,
    slide_type: str,
    slide_id: int,
    lesson_id: Optional[int],
    round_num: Optional[int],
    feedback_json: Optional[dict] = None,
) -> None:
    """Upsert current slide position; push old position to back-history first."""
    existing = get_position(db, username)
    if existing:
        max_pos = (
            db.query(func.max(SlideHistory.position))
            .filter(SlideHistory.username == username, SlideHistory.direction == "back")
            .scalar()
            or 0
        )
        db.add(
            SlideHistory(
                username=username,
                position=max_pos + 1,
                slide_type=existing.slide_type,
                slide_id=existing.slide_id,
                lesson_id=existing.lesson_id,
                round_num=existing.round_num,
                feedback_json=existing.feedback_json,
                direction="back",
            )
        )
        existing.slide_type = slide_type
        existing.slide_id = slide_id
        existing.lesson_id = lesson_id
        existing.round_num = round_num
        existing.feedback_json = feedback_json
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(
            UserSlidePosition(
                username=username,
                slide_type=slide_type,
                slide_id=slide_id,
                lesson_id=lesson_id,
                round_num=round_num,
                feedback_json=feedback_json,
            )
        )
    db.commit()


def save_feedback(db: Session, username: str, feedback_json: dict) -> None:
    """Update feedback_json on the current position after quiz grading."""
    existing = get_position(db, username)
    if existing:
        existing.feedback_json = feedback_json
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()


def push_to_history(
    db: Session,
    username: str,
    slide_type: str,
    slide_id: int,
    lesson_id: Optional[int],
    round_num: Optional[int],
    feedback_json: Optional[dict],
    direction: str,
) -> None:
    """Push a slide onto the history stack for the given direction."""
    max_pos = (
        db.query(func.max(SlideHistory.position))
        .filter(SlideHistory.username == username, SlideHistory.direction == direction)
        .scalar()
        or 0
    )
    db.add(
        SlideHistory(
            username=username,
            position=max_pos + 1,
            slide_type=slide_type,
            slide_id=slide_id,
            lesson_id=lesson_id,
            round_num=round_num,
            feedback_json=feedback_json,
            direction=direction,
        )
    )
    db.commit()


def pop_from_history(db: Session, username: str, direction: str) -> Optional[SlideHistory]:
    """Pop the most recent entry from the history stack for the given direction."""
    row = (
        db.query(SlideHistory)
        .filter(SlideHistory.username == username, SlideHistory.direction == direction)
        .order_by(SlideHistory.position.desc())
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
    return row


def get_history_depth(db: Session, username: str) -> int:
    """Count back-history entries for the user."""
    return (
        db.query(SlideHistory)
        .filter(SlideHistory.username == username, SlideHistory.direction == "back")
        .count()
    )


def push_to_forward(
    db: Session,
    username: str,
    slide_type: str,
    slide_id: int,
    lesson_id: Optional[int],
    round_num: Optional[int],
    feedback_json: Optional[dict],
) -> None:
    """Push a slide onto the forward stack."""
    push_to_history(db, username, slide_type, slide_id, lesson_id, round_num, feedback_json, "forward")


def pop_from_forward(db: Session, username: str) -> Optional[SlideHistory]:
    """Pop the most recent entry from the forward stack."""
    return pop_from_history(db, username, "forward")


def clear_forward(db: Session, username: str) -> None:
    """Clear all forward-stack entries for the user."""
    db.query(SlideHistory).filter(
        SlideHistory.username == username, SlideHistory.direction == "forward"
    ).delete()
    db.commit()


def go_back(db: Session, username: str) -> Optional[SlideHistory]:
    """Move back one step: push current to forward, pop from back-history, update current."""
    current = get_position(db, username)
    if not current:
        return None

    prev = (
        db.query(SlideHistory)
        .filter(SlideHistory.username == username, SlideHistory.direction == "back")
        .order_by(SlideHistory.position.desc())
        .first()
    )
    if not prev:
        return None

    max_fwd = (
        db.query(func.max(SlideHistory.position))
        .filter(SlideHistory.username == username, SlideHistory.direction == "forward")
        .scalar()
        or 0
    )
    db.add(
        SlideHistory(
            username=username,
            position=max_fwd + 1,
            slide_type=current.slide_type,
            slide_id=current.slide_id,
            lesson_id=current.lesson_id,
            round_num=current.round_num,
            feedback_json=current.feedback_json,
            direction="forward",
        )
    )

    prev_slide_type = prev.slide_type
    prev_slide_id = prev.slide_id
    prev_lesson_id = prev.lesson_id
    prev_round_num = prev.round_num
    prev_feedback_json = prev.feedback_json

    db.delete(prev)

    current.slide_type = prev_slide_type
    current.slide_id = prev_slide_id
    current.lesson_id = prev_lesson_id
    current.round_num = prev_round_num
    current.feedback_json = prev_feedback_json
    current.updated_at = datetime.now(timezone.utc)

    db.commit()
    return prev
