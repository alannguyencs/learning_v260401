"""CRUD operations for user_slide_like."""

from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.content import Book, Chapter, ChapterQuiz, Lesson
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


def get_liked_quizzes_with_context(
    db: Session, username: str
) -> List[Tuple[ChapterQuiz, Lesson, Book, "UserSlideLike"]]:
    """Return (quiz, lesson, book, like) rows for all quizzes the user liked, newest first."""
    return (
        db.query(UserSlideLike, ChapterQuiz, Lesson, Book)
        .join(ChapterQuiz, ChapterQuiz.id == UserSlideLike.quiz_id)
        .join(Chapter, Chapter.id == ChapterQuiz.chapter_id)
        .join(Lesson, Lesson.id == Chapter.lesson_id)
        .join(Book, Book.book_id == Lesson.book_id)
        .filter(UserSlideLike.username == username)
        .order_by(UserSlideLike.liked_at.desc(), UserSlideLike.id.desc())
        .all()
    )
