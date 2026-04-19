"""CRUD operations for user_slide_like (polymorphic: quizzes + chapters)."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.content import Book, Chapter, ChapterQuiz, Lesson
from src.models.slide_like import UserSlideLike


# ─── Quiz likes ──────────────────────────────────────────────────────────────


def add_like(db: Session, username: str, quiz_id: int) -> None:
    """Insert a quiz-like row; idempotent on (username, quiz_id)."""
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
    """Delete a quiz-like row; no-op if absent."""
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
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.quiz_id.isnot(None),
        )
        .order_by(UserSlideLike.liked_at.desc(), UserSlideLike.id.desc())
        .all()
    )
    return [row.quiz_id for row in rows]


def get_liked_quizzes_with_context(
    db: Session, username: str
) -> List[Tuple["UserSlideLike", ChapterQuiz, Lesson, Book]]:
    """Return (like, quiz, lesson, book) rows for all quizzes the user liked, newest first."""
    return (
        db.query(UserSlideLike, ChapterQuiz, Lesson, Book)
        .join(ChapterQuiz, ChapterQuiz.id == UserSlideLike.quiz_id)
        .join(Chapter, Chapter.id == ChapterQuiz.chapter_id)
        .join(Lesson, Lesson.id == Chapter.lesson_id)
        .join(Book, Book.book_id == Lesson.book_id)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.quiz_id.isnot(None),
        )
        .order_by(UserSlideLike.liked_at.desc(), UserSlideLike.id.desc())
        .all()
    )


# ─── Chapter likes ───────────────────────────────────────────────────────────


def add_chapter_like(db: Session, username: str, chapter_id: int) -> None:
    """Insert a chapter-like row; idempotent on (username, chapter_id)."""
    db.execute(
        text(
            """
            INSERT INTO user_slide_like (username, chapter_id)
            VALUES (:username, :chapter_id)
            ON CONFLICT (username, chapter_id) DO NOTHING
            """
        ),
        {"username": username, "chapter_id": chapter_id},
    )
    db.commit()


def remove_chapter_like(db: Session, username: str, chapter_id: int) -> None:
    """Delete a chapter-like row; no-op if absent."""
    db.execute(
        text(
            """
            DELETE FROM user_slide_like
            WHERE username = :username AND chapter_id = :chapter_id
            """
        ),
        {"username": username, "chapter_id": chapter_id},
    )
    db.commit()


def is_chapter_liked(db: Session, username: str, chapter_id: int) -> bool:
    """Return True if the user has liked the chapter."""
    row = (
        db.query(UserSlideLike)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.chapter_id == chapter_id,
        )
        .first()
    )
    return row is not None


def get_liked_chapter_ids(db: Session, username: str) -> List[int]:
    """Return all chapter IDs the user has liked, newest first."""
    rows = (
        db.query(UserSlideLike.chapter_id)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.chapter_id.isnot(None),
        )
        .order_by(UserSlideLike.liked_at.desc(), UserSlideLike.id.desc())
        .all()
    )
    return [row.chapter_id for row in rows]


# ─── Interleaved listing ─────────────────────────────────────────────────────


@dataclass
class LikedItemRow:  # pylint: disable=too-many-instance-attributes
    """A type-tagged row from the interleaved liked-items listing."""

    kind: Literal["quiz", "chapter"]
    like_id: int
    liked_at: datetime
    book_id: str
    book_title: str
    lesson_id: int
    lesson_title: str
    lesson_index: int
    # populated for kind=="quiz"
    quiz: Optional[ChapterQuiz]
    # populated for kind=="chapter"
    chapter: Optional[Chapter]


def get_liked_items_with_context(db: Session, username: str) -> List[LikedItemRow]:
    """Return an interleaved list of liked quizzes and chapters, newest first."""
    quiz_rows = (
        db.query(UserSlideLike, ChapterQuiz, Lesson, Book)
        .join(ChapterQuiz, ChapterQuiz.id == UserSlideLike.quiz_id)
        .join(Chapter, Chapter.id == ChapterQuiz.chapter_id)
        .join(Lesson, Lesson.id == Chapter.lesson_id)
        .join(Book, Book.book_id == Lesson.book_id)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.quiz_id.isnot(None),
        )
        .all()
    )

    chapter_rows = (
        db.query(UserSlideLike, Chapter, Lesson, Book)
        .join(Chapter, Chapter.id == UserSlideLike.chapter_id)
        .join(Lesson, Lesson.id == Chapter.lesson_id)
        .join(Book, Book.book_id == Lesson.book_id)
        .filter(
            UserSlideLike.username == username,
            UserSlideLike.chapter_id.isnot(None),
        )
        .all()
    )

    items: List[LikedItemRow] = []
    for like, quiz, lesson, book in quiz_rows:
        items.append(
            LikedItemRow(
                kind="quiz",
                like_id=like.id,
                liked_at=like.liked_at,
                book_id=book.book_id,
                book_title=book.title,
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                lesson_index=lesson.lesson_index,
                quiz=quiz,
                chapter=None,
            )
        )
    for like, chapter, lesson, book in chapter_rows:
        items.append(
            LikedItemRow(
                kind="chapter",
                like_id=like.id,
                liked_at=like.liked_at,
                book_id=book.book_id,
                book_title=book.title,
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                lesson_index=lesson.lesson_index,
                quiz=None,
                chapter=chapter,
            )
        )

    items.sort(key=lambda r: (r.liked_at, r.like_id), reverse=True)
    return items
