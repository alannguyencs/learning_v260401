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
      - quiz_answer_log        → ANSWER  (with forgetting_rate from user_quiz_recall)
      - lesson_revision_rounds → ROUND CREATED (Rn status)
    """
    sql = text(
        """
        SELECT event_time, action, book_id, lesson_index, lesson_title,
               chapter_id, answer_result, forgetting_rate
        FROM (

            SELECT ucp.learnt_at AS event_time,
                   'LEARNT CHAPTER' AS action,
                   l.book_id,
                   l.lesson_index,
                   l.title AS lesson_title,
                   CAST(c.id AS INTEGER) AS chapter_id,
                   CAST(NULL AS VARCHAR) AS answer_result,
                   CAST(NULL AS DOUBLE PRECISION) AS forgetting_rate
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
            "forgetting_rate": (
                round(float(row.forgetting_rate), 2) if row.forgetting_rate is not None else None
            ),
        }
        for row in rows
    ]


def get_learning_progress(db: Session, username: str) -> list[dict]:
    """
    Return per-lesson progress metrics for the user.

    Aggregates chapters progress, latest revision round, quiz accuracy,
    and average recall strength per lesson, grouped by book.
    """
    sql = text(
        """
        WITH chapter_progress AS (
            SELECT c.lesson_id,
                   COUNT(c.id) AS total_chapters,
                   COUNT(ucp.id) AS learnt_chapters
            FROM chapters c
            LEFT JOIN user_chapter_progress ucp
                ON ucp.chapter_id = c.id AND ucp.username = :username
            GROUP BY c.lesson_id
        ),
        latest_round AS (
            SELECT lrr.lesson_id, lrr.round_num, lrr.status,
                   lrr.quizzes_in_round, lrr.quizzes_answered
            FROM lesson_revision_rounds lrr
            INNER JOIN (
                SELECT lesson_id, MAX(round_num) AS max_round
                FROM lesson_revision_rounds
                WHERE username = :username
                GROUP BY lesson_id
            ) mx ON mx.lesson_id = lrr.lesson_id
                AND mx.max_round = lrr.round_num
            WHERE lrr.username = :username
        ),
        quiz_accuracy AS (
            SELECT lesson_id,
                   COUNT(*) AS total_answers,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct_answers
            FROM quiz_answer_log
            WHERE username = :username
            GROUP BY lesson_id
        ),
        avg_recall AS (
            SELECT c.lesson_id,
                   ROUND(AVG(uqr.forgetting_rate), 2)
                       AS avg_forgetting_rate
            FROM user_quiz_recall uqr
            JOIN chapter_quizzes cq ON cq.id = uqr.quiz_id
            JOIN chapters c ON c.id = cq.chapter_id
            WHERE uqr.username = :username
            GROUP BY c.lesson_id
        )
        SELECT l.id AS lesson_id,
               l.book_id,
               b.title AS book_title,
               l.lesson_index,
               l.title AS lesson_title,
               COALESCE(cp.total_chapters, 0) AS total_chapters,
               COALESCE(cp.learnt_chapters, 0) AS learnt_chapters,
               lr.round_num,
               lr.status AS round_status,
               lr.quizzes_in_round,
               lr.quizzes_answered AS round_quizzes_answered,
               COALESCE(qa.total_answers, 0) AS total_answers,
               COALESCE(qa.correct_answers, 0) AS correct_answers,
               ar.avg_forgetting_rate
        FROM lessons l
        JOIN books b ON b.book_id = l.book_id
        LEFT JOIN chapter_progress cp ON cp.lesson_id = l.id
        LEFT JOIN latest_round lr ON lr.lesson_id = l.id
        LEFT JOIN quiz_accuracy qa ON qa.lesson_id = l.id
        LEFT JOIN avg_recall ar ON ar.lesson_id = l.id
        ORDER BY l.book_id, l.lesson_index
        """
    )

    rows = db.execute(sql, {"username": username}).fetchall()
    return [
        {
            "lesson_id": row.lesson_id,
            "book_id": row.book_id,
            "book_title": row.book_title,
            "lesson_index": row.lesson_index,
            "lesson_title": row.lesson_title,
            "total_chapters": int(row.total_chapters),
            "learnt_chapters": int(row.learnt_chapters),
            "round_num": row.round_num,
            "round_status": row.round_status,
            "quizzes_in_round": row.quizzes_in_round,
            "round_quizzes_answered": row.round_quizzes_answered,
            "total_answers": int(row.total_answers),
            "correct_answers": int(row.correct_answers),
            "avg_forgetting_rate": (
                float(row.avg_forgetting_rate) if row.avg_forgetting_rate is not None else None
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
