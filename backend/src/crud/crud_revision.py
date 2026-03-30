"""CRUD operations for revision scheduling: LessonRevisionRound, UserQuizRecall."""

from typing import Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.revision_scheduling import LessonRevisionRound, UserQuizRecall


def get_open_round(
    db: Session, username: str, lesson_id: int, round_num: int
) -> Optional[LessonRevisionRound]:
    """Return the open round for (username, lesson_id, round_num), or None."""
    return (
        db.query(LessonRevisionRound)
        .filter(
            LessonRevisionRound.username == username,
            LessonRevisionRound.lesson_id == lesson_id,
            LessonRevisionRound.round_num == round_num,
            LessonRevisionRound.status == "open",
        )
        .first()
    )


def get_latest_round(db: Session, username: str, lesson_id: int) -> Optional[LessonRevisionRound]:
    """Return the round with the highest round_num for (username, lesson_id)."""
    return (
        db.query(LessonRevisionRound)
        .filter(
            LessonRevisionRound.username == username,
            LessonRevisionRound.lesson_id == lesson_id,
        )
        .order_by(LessonRevisionRound.round_num.desc())
        .first()
    )


def create_round(
    db: Session,
    username: str,
    lesson_id: int,
    round_num: int,
    due_at_lesson_count: int,
    quizzes_in_round: int,
) -> LessonRevisionRound:
    """Insert a new revision round and return it."""
    row = LessonRevisionRound(
        username=username,
        lesson_id=lesson_id,
        round_num=round_num,
        due_at_lesson_count=due_at_lesson_count,
        quizzes_in_round=quizzes_in_round,
        status="open",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def increment_round_quiz_count(db: Session, round_id: int, delta: int) -> None:
    """Increment quizzes_in_round by delta."""
    db.execute(
        text(
            "UPDATE lesson_revision_rounds "
            "SET quizzes_in_round = quizzes_in_round + :delta "
            "WHERE id = :round_id"
        ),
        {"delta": delta, "round_id": round_id},
    )
    db.commit()


def increment_round_answered(db: Session, round_id: int) -> LessonRevisionRound:
    """Increment quizzes_answered by 1 and return the updated row."""
    db.execute(
        text(
            "UPDATE lesson_revision_rounds "
            "SET quizzes_answered = quizzes_answered + 1 "
            "WHERE id = :round_id"
        ),
        {"round_id": round_id},
    )
    db.commit()
    return db.query(LessonRevisionRound).filter(LessonRevisionRound.id == round_id).first()


def complete_round(db: Session, round_id: int, completed_at_lesson_count: int) -> None:
    """Mark a round as done and record the completion lesson count."""
    db.execute(
        text(
            "UPDATE lesson_revision_rounds "
            "SET status = 'done', completed_at_lesson_count = :completed "
            "WHERE id = :round_id"
        ),
        {"completed": completed_at_lesson_count, "round_id": round_id},
    )
    db.commit()


def get_due_rounds(db: Session, username: str, lesson_count: int) -> list:
    """Return all open rounds where due_at_lesson_count <= lesson_count."""
    return (
        db.query(LessonRevisionRound)
        .filter(
            LessonRevisionRound.username == username,
            LessonRevisionRound.status == "open",
            LessonRevisionRound.due_at_lesson_count <= lesson_count,
        )
        .all()
    )


def get_answered_quiz_ids_in_round(
    db: Session, username: str, lesson_id: int, round_num: int
) -> Set[int]:
    """
    Return quiz_ids already reviewed in a given round.

    A quiz counts as answered in this round if its last_reviewed_lesson_count
    is >= the round's due_at_lesson_count.
    """
    round_row = get_open_round(db, username, lesson_id, round_num)
    if round_row is None:
        return set()

    due_at = round_row.due_at_lesson_count
    rows = (
        db.query(UserQuizRecall.quiz_id)
        .filter(
            UserQuizRecall.username == username,
            UserQuizRecall.last_reviewed_lesson_count >= due_at,
        )
        .all()
    )
    return {row.quiz_id for row in rows}


def upsert_quiz_recall(
    db: Session,
    username: str,
    quiz_id: int,
    forgetting_rate: float,
    lesson_count: int,
) -> UserQuizRecall:
    """Insert or update a UserQuizRecall row."""
    db.execute(
        text(
            """
            INSERT INTO user_quiz_recall
                (username, quiz_id, forgetting_rate, last_reviewed_lesson_count, review_count)
            VALUES
                (:username, :quiz_id, :forgetting_rate, :lesson_count, 1)
            ON CONFLICT (username, quiz_id) DO UPDATE
            SET forgetting_rate = :forgetting_rate,
                last_reviewed_lesson_count = :lesson_count,
                review_count = user_quiz_recall.review_count + 1
            """
        ),
        {
            "username": username,
            "quiz_id": quiz_id,
            "forgetting_rate": forgetting_rate,
            "lesson_count": lesson_count,
        },
    )
    db.commit()
    return get_quiz_recall(db, username, quiz_id)


def get_quiz_recall(db: Session, username: str, quiz_id: int) -> Optional[UserQuizRecall]:
    """Return the recall row for (username, quiz_id), or None."""
    return (
        db.query(UserQuizRecall)
        .filter(
            UserQuizRecall.username == username,
            UserQuizRecall.quiz_id == quiz_id,
        )
        .first()
    )


def get_quiz_recalls_for_lesson(db: Session, username: str, lesson_id: int) -> list:
    """Return all recall rows for quizzes in a lesson (for weakest-first ordering)."""
    from src.models.content import ChapterQuiz, Chapter  # pylint: disable=import-outside-toplevel

    return (
        db.query(UserQuizRecall)
        .join(ChapterQuiz, UserQuizRecall.quiz_id == ChapterQuiz.id)
        .join(Chapter, ChapterQuiz.chapter_id == Chapter.id)
        .filter(
            UserQuizRecall.username == username,
            Chapter.lesson_id == lesson_id,
        )
        .all()
    )
