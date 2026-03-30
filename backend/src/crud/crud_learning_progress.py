"""CRUD operations for learning progress: UserChapterProgress, UserLessonCount."""

from typing import Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.content import Chapter
from src.models.learning_progress import UserChapterProgress, UserLessonCount


def mark_chapter_learnt(db: Session, username: str, chapter_id: int) -> None:
    """Record a chapter as learnt for the user. Ignores duplicates."""
    existing = (
        db.query(UserChapterProgress)
        .filter(
            UserChapterProgress.username == username,
            UserChapterProgress.chapter_id == chapter_id,
        )
        .first()
    )
    if not existing:
        db.add(UserChapterProgress(username=username, chapter_id=chapter_id))
        db.commit()


def is_chapter_learnt(db: Session, username: str, chapter_id: int) -> bool:
    """Return True if the user has marked this chapter as learnt."""
    return (
        db.query(UserChapterProgress)
        .filter(
            UserChapterProgress.username == username,
            UserChapterProgress.chapter_id == chapter_id,
        )
        .first()
        is not None
    )


def count_learnt_chapters_in_lesson(db: Session, username: str, lesson_id: int) -> int:
    """Count how many chapters in the lesson the user has marked as learnt."""
    return (
        db.query(UserChapterProgress)
        .join(Chapter, UserChapterProgress.chapter_id == Chapter.id)
        .filter(
            UserChapterProgress.username == username,
            Chapter.lesson_id == lesson_id,
        )
        .count()
    )


def get_lesson_count(db: Session, username: str) -> int:
    """Return the user's total fully-learnt lesson count. Returns 0 if no row yet."""
    row = db.query(UserLessonCount).filter(UserLessonCount.username == username).first()
    return row.total_lessons_learnt if row else 0


def increment_lesson_count(db: Session, username: str) -> int:
    """Increment total_lessons_learnt by 1, inserting the row if absent. Returns new value."""
    db.execute(
        text(
            """
            INSERT INTO user_lesson_count (username, total_lessons_learnt)
            VALUES (:username, 1)
            ON CONFLICT (username) DO UPDATE
            SET total_lessons_learnt = user_lesson_count.total_lessons_learnt + 1
            """
        ),
        {"username": username},
    )
    db.commit()
    return get_lesson_count(db, username)


def get_learnt_chapter_ids_for_user(db: Session, username: str) -> Set[int]:
    """Return all chapter IDs the user has marked as learnt."""
    rows = (
        db.query(UserChapterProgress.chapter_id)
        .filter(UserChapterProgress.username == username)
        .all()
    )
    return {row.chapter_id for row in rows}
