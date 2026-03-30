"""RevisionService: manages revision rounds and quiz recall tracking."""

import math
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from src.crud import crud_revision
from src.crud.crud_content import get_lesson_quiz_count

MEMORIZE_DIVISOR = 10
MAX_FORGETTING_RATE = 1.5


@dataclass
class QuizResponseResult:
    """Result of recording a quiz response."""

    round_done: bool
    next_round_num: Optional[int]
    next_round_due_at: Optional[int]


class RevisionService:
    """Service for revision scheduling and quiz recall management."""

    @staticmethod
    def on_chapter_learnt(
        db: Session,
        username: str,
        lesson_id: int,
        chapter_quiz_ids: List[int],
        lesson_count: int,
    ) -> None:
        """
        Distribute new chapter quizzes into the correct revision round.

        - Case A: No R0 exists → create R0 due immediately.
        - Case B: R0 is open → increment its quizzes_in_round.
        - Case C: R0 is done → find/create next open round and increment.
        """
        if not chapter_quiz_ids:
            return

        delta = len(chapter_quiz_ids)

        r0 = crud_revision.get_open_round(db, username, lesson_id, 0)
        if r0 is not None:
            # Case B: R0 open
            crud_revision.increment_round_quiz_count(db, r0.id, delta)
            return

        latest = crud_revision.get_latest_round(db, username, lesson_id)
        if latest is None:
            # Case A: no round at all — create R0
            crud_revision.create_round(
                db,
                username=username,
                lesson_id=lesson_id,
                round_num=0,
                due_at_lesson_count=lesson_count,
                quizzes_in_round=delta,
            )
            return

        # Case C: R0 (or some earlier round) is done — find/create next open round
        next_round_num = latest.round_num + 1 if latest.status == "done" else latest.round_num
        open_round = crud_revision.get_open_round(db, username, lesson_id, next_round_num)
        if open_round is not None:
            crud_revision.increment_round_quiz_count(db, open_round.id, delta)
        else:
            # Due at the interval calculated when R0 completed (use latest completed)
            due_at = latest.completed_at_lesson_count or lesson_count
            due_at += 2 ** (next_round_num + 1)
            crud_revision.create_round(
                db,
                username=username,
                lesson_id=lesson_id,
                round_num=next_round_num,
                due_at_lesson_count=due_at,
                quizzes_in_round=delta,
            )

    @staticmethod
    def record_quiz_response(
        db: Session,
        username: str,
        quiz_id: int,
        lesson_id: int,
        round_num: int,
        is_correct: Optional[bool],
        lesson_count: int,
    ) -> QuizResponseResult:
        """
        Record a quiz answer (or skip) and advance the revision round if complete.

        is_correct=None means skip: no recall update, quizzes_answered not incremented.
        """
        round_row = crud_revision.get_open_round(db, username, lesson_id, round_num)

        if is_correct is not None:
            # Update MEMORIZE forgetting rate
            existing = crud_revision.get_quiz_recall(db, username, quiz_id)
            current_rate = existing.forgetting_rate if existing else 1.0
            if is_correct:
                new_rate = current_rate * 0.7
            else:
                new_rate = min(current_rate * 1.2, MAX_FORGETTING_RATE)
            crud_revision.upsert_quiz_recall(db, username, quiz_id, new_rate, lesson_count)

            if round_row is not None:
                round_row = crud_revision.increment_round_answered(db, round_row.id)

        if round_row is None:
            return QuizResponseResult(
                round_done=False, next_round_num=None, next_round_due_at=None
            )

        quizzes_in = round_row.quizzes_in_round
        quizzes_ans = round_row.quizzes_answered
        threshold_met = quizzes_in > 0 and (quizzes_ans / quizzes_in) > 0.50

        if not threshold_met:
            return QuizResponseResult(
                round_done=False, next_round_num=None, next_round_due_at=None
            )

        # Complete this round and schedule the next
        crud_revision.complete_round(db, round_row.id, lesson_count)

        next_round_num = round_num + 1
        interval = 2 ** (round_num + 1)
        next_due_at = lesson_count + interval

        total_quizzes = get_lesson_quiz_count(db, lesson_id)
        crud_revision.create_round(
            db,
            username=username,
            lesson_id=lesson_id,
            round_num=next_round_num,
            due_at_lesson_count=next_due_at,
            quizzes_in_round=total_quizzes,
        )

        return QuizResponseResult(
            round_done=True,
            next_round_num=next_round_num,
            next_round_due_at=next_due_at,
        )

    @staticmethod
    def compute_recall(forgetting_rate: float, lessons_elapsed: int) -> float:
        """m(t) = exp(-forgetting_rate * lessons_elapsed / MEMORIZE_DIVISOR)."""
        return math.exp(-forgetting_rate * max(lessons_elapsed, 0) / MEMORIZE_DIVISOR)
