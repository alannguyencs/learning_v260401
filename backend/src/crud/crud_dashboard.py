"""CRUD operations for the dashboard activity log."""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.slide_management import QuizAnswerLog


def log_quiz_answer(
    db: Session,
    username: str,
    quiz_id: int,
    lesson_id: int,
    round_num: int,
    is_correct: bool,
) -> None:
    """Append one row to quiz_answer_log."""
    db.add(
        QuizAnswerLog(
            username=username,
            quiz_id=quiz_id,
            lesson_id=lesson_id,
            round_num=round_num,
            is_correct=is_correct,
        )
    )
    db.commit()


def get_activity_log(db: Session, username: str) -> list[dict]:
    """
    Return all interaction events for the user sorted by event_time ASC.

    Unions four event sources:
      - user_chapter_progress  → LEARNT CHAPTER
      - quiz_skip_log          → SKIP
      - quiz_answer_log        → ANSWER  (with recall_rate from user_quiz_recall)
      - lesson_revision_rounds → ROUND CREATED (Rn status)
    """
    sql = text(
        """
        SELECT event_time, action, book_id, lesson_index, lesson_title,
               chapter_id, answer_result, recall_rate
        FROM (

            SELECT ucp.learnt_at AS event_time,
                   'LEARNT CHAPTER' AS action,
                   l.book_id,
                   l.lesson_index,
                   l.title AS lesson_title,
                   CAST(c.id AS INTEGER) AS chapter_id,
                   CAST(NULL AS VARCHAR) AS answer_result,
                   CAST(NULL AS DOUBLE PRECISION) AS recall_rate
            FROM user_chapter_progress ucp
            JOIN chapters c ON c.id = ucp.chapter_id
            JOIN lessons l ON l.id = c.lesson_id
            WHERE ucp.username = :username

            UNION ALL

            SELECT qsl.skipped_at,
                   'SKIP',
                   l.book_id,
                   l.lesson_index,
                   l.title,
                   CAST(cq.chapter_id AS INTEGER),
                   CAST(NULL AS VARCHAR),
                   CAST(NULL AS DOUBLE PRECISION)
            FROM quiz_skip_log qsl
            JOIN chapter_quizzes cq ON cq.id = qsl.quiz_id
            JOIN lessons l ON l.id = qsl.lesson_id
            WHERE qsl.username = :username

            UNION ALL

            SELECT qal.answered_at,
                   'ANSWER',
                   l.book_id,
                   l.lesson_index,
                   l.title,
                   CAST(cq.chapter_id AS INTEGER),
                   CASE WHEN qal.is_correct THEN 'correct' ELSE 'wrong' END,
                   uqr.forgetting_rate
            FROM quiz_answer_log qal
            JOIN chapter_quizzes cq ON cq.id = qal.quiz_id
            JOIN lessons l ON l.id = qal.lesson_id
            LEFT JOIN user_quiz_recall uqr
                ON uqr.username = qal.username AND uqr.quiz_id = qal.quiz_id
            WHERE qal.username = :username

            UNION ALL

            SELECT lrr.created_at,
                   'ROUND CREATED (R' || CAST(lrr.round_num AS VARCHAR) || ')',
                   l.book_id,
                   l.lesson_index,
                   l.title,
                   CAST(NULL AS INTEGER),
                   CAST(NULL AS VARCHAR),
                   CAST(NULL AS DOUBLE PRECISION)
            FROM lesson_revision_rounds lrr
            JOIN lessons l ON l.id = lrr.lesson_id
            WHERE lrr.username = :username

        ) t
        ORDER BY event_time ASC
        """
    )

    rows = db.execute(sql, {"username": username}).fetchall()
    return [
        {
            "event_time": row.event_time,
            "action": row.action,
            "book_id": row.book_id,
            "lesson_index": row.lesson_index,
            "lesson_title": row.lesson_title,
            "chapter_id": row.chapter_id,
            "answer_result": row.answer_result,
            "recall_rate": (
                round(float(row.recall_rate), 2) if row.recall_rate is not None else None
            ),
        }
        for row in rows
    ]


def get_activity_log_count(db: Session, username: str) -> Optional[int]:
    """Return total number of activity events for a user."""
    result = db.execute(
        text(
            """
            SELECT COUNT(*) FROM (
                SELECT 1 FROM user_chapter_progress WHERE username = :username
                UNION ALL
                SELECT 1 FROM quiz_skip_log WHERE username = :username
                UNION ALL
                SELECT 1 FROM quiz_answer_log WHERE username = :username
                UNION ALL
                SELECT 1 FROM lesson_revision_rounds WHERE username = :username
            ) t
            """
        ),
        {"username": username},
    ).scalar()
    return result
