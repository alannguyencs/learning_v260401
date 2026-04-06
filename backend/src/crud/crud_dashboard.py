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


def _compute_accuracy_trend(answers: list[bool]) -> list[int]:
    """
    Compute sliding-window accuracy trend from a chronological list of answers.

    Takes the most recent 119 answers. Creates up to 20 windows of 100,
    each sliding by 1. Returns a list of integers (correct per 100).
    """
    n = len(answers)
    if n < 100:
        return []
    window_count = min(n - 99, 20)
    offset = n - 99 - window_count
    correct_in_first = sum(answers[offset : offset + 100])  # noqa: E203
    trend = [correct_in_first]
    for i in range(1, window_count):
        leaving = answers[offset + i - 1]
        entering = answers[offset + i + 99]
        correct_in_first += int(entering) - int(leaving)
        trend.append(correct_in_first)
    return trend


def get_learning_progress(db: Session, username: str) -> list[dict]:
    """
    Return per-book progress with lesson table and accuracy trendline.

    Each book entry contains:
      - lessons: list of {lesson_title, round_num, round_status,
                          total_answers, correct_answers}
      - accuracy_trend: list of up to 20 ints (correct per 100)
    """
    lesson_sql = text(
        """
        WITH latest_round AS (
            SELECT lrr.lesson_id, lrr.round_num, lrr.status
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
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END)
                       AS correct_answers
            FROM quiz_answer_log
            WHERE username = :username
            GROUP BY lesson_id
        )
        SELECT l.id AS lesson_id,
               l.book_id,
               b.title AS book_title,
               l.title AS lesson_title,
               lr.round_num,
               lr.status AS round_status,
               COALESCE(qa.total_answers, 0) AS total_answers,
               COALESCE(qa.correct_answers, 0) AS correct_answers
        FROM lessons l
        JOIN books b ON b.book_id = l.book_id
        LEFT JOIN latest_round lr ON lr.lesson_id = l.id
        LEFT JOIN quiz_accuracy qa ON qa.lesson_id = l.id
        ORDER BY l.book_id, l.lesson_index
        """
    )
    lesson_rows = db.execute(lesson_sql, {"username": username}).fetchall()

    trend_sql = text(
        """
        SELECT qal.is_correct, l.book_id
        FROM quiz_answer_log qal
        JOIN lessons l ON l.id = qal.lesson_id
        WHERE qal.username = :username
        ORDER BY l.book_id, qal.answered_at DESC
        """
    )
    trend_rows = db.execute(trend_sql, {"username": username}).fetchall()

    book_answers: dict[str, list[bool]] = {}
    for row in trend_rows:
        book_answers.setdefault(row.book_id, []).append(bool(row.is_correct))
    for answers in book_answers.values():
        answers.reverse()
        if len(answers) > 119:
            del answers[: len(answers) - 119]

    books: dict[str, dict] = {}
    for row in lesson_rows:
        if row.book_id not in books:
            books[row.book_id] = {
                "book_id": row.book_id,
                "book_title": row.book_title,
                "lessons": [],
                "accuracy_trend": [],
            }
        books[row.book_id]["lessons"].append(
            {
                "lesson_title": row.lesson_title,
                "round_num": row.round_num,
                "round_status": row.round_status,
                "total_answers": int(row.total_answers),
                "correct_answers": int(row.correct_answers),
            }
        )

    for book_id, book in books.items():
        answers = book_answers.get(book_id, [])
        book["accuracy_trend"] = _compute_accuracy_trend(answers)

    return list(books.values())


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
