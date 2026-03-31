"""CRUD operations for slide selection: chapter navigation and skip log."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.crud.crud_learning_progress import get_learnt_chapter_ids_for_user
from src.crud.crud_revision import get_answered_quiz_ids_in_round
from src.models.content import Book, Chapter, ChapterQuiz, Lesson
from src.models.slide_management import QuizSkipLog


def get_next_chapter_in_book(db: Session, username: str, book_id: str) -> Optional[Chapter]:
    """Find the first chapter in book order that the user has not yet learnt."""
    learnt_ids = get_learnt_chapter_ids_for_user(db, username)
    return (
        db.query(Chapter)
        .join(Lesson, Chapter.lesson_id == Lesson.id)
        .filter(
            Lesson.book_id == book_id,
            Chapter.id.notin_(learnt_ids) if learnt_ids else True,
        )
        .order_by(Lesson.lesson_index, Chapter.chapter_index)
        .first()
    )


def get_next_chapters_all_books(db: Session, username: str) -> List[Chapter]:
    """For each book, find the first unlearnt chapter. Returns one per book."""
    books = db.query(Book).order_by(Book.book_id).all()
    result = []
    for book in books:
        chapter = get_next_chapter_in_book(db, username, book.book_id)
        if chapter:
            result.append(chapter)
    return result


def get_eligible_quiz_ids_for_round(
    db: Session, username: str, lesson_id: int, round_num: int
) -> List[int]:
    """Return quiz IDs for the lesson not yet answered or skipped in this round.

    Only includes quizzes from chapters the user has already learnt.
    """
    learnt_chapter_ids = get_learnt_chapter_ids_for_user(db, username)
    all_quizzes = (
        db.query(ChapterQuiz)
        .join(Chapter, ChapterQuiz.chapter_id == Chapter.id)
        .filter(
            Chapter.lesson_id == lesson_id,
            ChapterQuiz.chapter_id.in_(learnt_chapter_ids) if learnt_chapter_ids else False,
        )
        .all()
    )
    all_ids = {q.id for q in all_quizzes}

    answered_ids = get_answered_quiz_ids_in_round(db, username, lesson_id, round_num)

    skipped_rows = db.query(QuizSkipLog.quiz_id).filter(QuizSkipLog.username == username).all()
    skipped_ids = {row.quiz_id for row in skipped_rows}

    return list(all_ids - answered_ids - skipped_ids)


def log_quiz_skip(
    db: Session, username: str, quiz_id: int, lesson_id: int, round_num: int
) -> None:
    """Record that a user skipped a quiz."""
    existing = (
        db.query(QuizSkipLog)
        .filter(QuizSkipLog.username == username, QuizSkipLog.quiz_id == quiz_id)
        .first()
    )
    if not existing:
        db.add(
            QuizSkipLog(
                username=username,
                quiz_id=quiz_id,
                lesson_id=lesson_id,
                round_num=round_num,
            )
        )
        db.commit()


def remove_quiz_skip(db: Session, username: str, quiz_id: int) -> None:
    """Remove a skip log entry when the quiz is answered."""
    db.query(QuizSkipLog).filter(
        QuizSkipLog.username == username,
        QuizSkipLog.quiz_id == quiz_id,
    ).delete()
    db.commit()


def get_skipped_quizzes(db: Session, username: str) -> List[dict]:
    """Return skipped quizzes ordered by skipped_at ASC (oldest first)."""
    rows = (
        db.query(QuizSkipLog)
        .filter(QuizSkipLog.username == username)
        .order_by(QuizSkipLog.skipped_at)
        .all()
    )
    return [
        {
            "quiz_id": row.quiz_id,
            "lesson_id": row.lesson_id,
            "round_num": row.round_num,
        }
        for row in rows
    ]
