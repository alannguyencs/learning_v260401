"""SlideSelector: implements the 3-tier slide priority algorithm."""

import random
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.crud import crud_learning_progress
from src.crud.crud_content import get_chapter_quiz, get_lesson
from src.crud.crud_revision import get_due_rounds, get_quiz_recall
from src.crud.crud_slides import (
    get_eligible_quiz_ids_for_round,
    get_next_chapter_in_book,
    get_next_chapters_all_books,
)
from src.models.content import Book, Chapter, Lesson
from src.service.revision_service import RevisionService


@dataclass
class SlideResult:
    """Result of the slide selection algorithm."""

    slide_type: str  # 'chapter', 'quiz', or 'none'
    chapter: Optional[dict]
    quiz: Optional[dict]
    has_previous: bool = False
    feedback: Optional[dict] = None


def _build_chapter_dict(db: Session, chapter: Chapter) -> dict:
    """Build a chapter dict enriched with lesson and book info."""
    lesson = db.query(Lesson).filter(Lesson.id == chapter.lesson_id).first()
    book = db.query(Book).filter(Book.book_id == lesson.book_id).first()
    return {
        "id": chapter.id,
        "lesson_id": chapter.lesson_id,
        "book_id": lesson.book_id,
        "book_title": book.title,
        "lesson_title": lesson.title,
        "lesson_index": lesson.lesson_index,
        "chapter_index": chapter.chapter_index,
        "title": chapter.title,
        "content": chapter.content,
    }


def _build_quiz_dict(db: Session, quiz_id: int, round_num: int, lesson_id: int) -> dict:
    """Build a quiz dict enriched with lesson and book info."""
    quiz = get_chapter_quiz(db, quiz_id)
    lesson = get_lesson(db, lesson_id)
    book = db.query(Book).filter(Book.book_id == lesson.book_id).first()
    return {
        "id": quiz.id,
        "chapter_id": quiz.chapter_id,
        "quiz_type": quiz.quiz_type,
        "question": quiz.question,
        "option_a": quiz.option_a,
        "option_b": quiz.option_b,
        "option_c": quiz.option_c,
        "option_d": quiz.option_d,
        "expected_answer": quiz.expected_answer,
        "round_num": round_num,
        "lesson_id": lesson_id,
        "lesson_title": lesson.title,
        "book_title": book.title,
        "section_name": quiz.section_name,
        "quiz_take_away": quiz.quiz_take_away,
        "quiz_metadata": quiz.quiz_metadata,
        "correct_options": quiz.correct_options,
    }


class SlideSelector:
    """Implements the slide priority algorithm: Group A → Group B → Tier 2."""

    @staticmethod
    def get_next_slide(db: Session, username: str, book_id: Optional[str] = None) -> SlideResult:
        """
        Return the next slide for the user.

        Priority:
        1. Due revision quizzes — Group A (non-skipped, weakest recall first)
        2. Due revision quizzes — Group B (skipped, oldest skip first)
        3. Next unlearnt chapter
        """
        lesson_count = crud_learning_progress.get_lesson_count(db, username)

        # Tier 1: due revision quizzes
        # Group A: non-skipped (served first, weakest recall)
        # Group B: skipped (served after Group A exhausted, oldest skip first)
        due_rounds = get_due_rounds(db, username, lesson_count)
        group_a = []
        group_b = []

        for round_row in due_rounds:
            # Activation gate: skip this lesson's quizzes until ALL its chapters are learnt
            if not crud_learning_progress.all_lesson_chapters_learnt(
                db, username, round_row.lesson_id
            ):
                continue
            # Book-priority rank: 0 for lessons whose book matches the filter, 1 otherwise.
            # When no book_id is provided, every round ranks 0 (no re-ordering).
            lesson = get_lesson(db, round_row.lesson_id)
            if book_id and lesson is not None and lesson.book_id != book_id:
                book_rank = 1
            else:
                book_rank = 0
            non_skipped, skipped = get_eligible_quiz_ids_for_round(
                db, username, round_row.lesson_id, round_row.round_num
            )
            for qid in non_skipped:
                recall = get_quiz_recall(db, username, qid)
                if recall is not None:
                    last_reviewed = recall.last_reviewed_lesson_count or 0
                    elapsed = lesson_count - last_reviewed
                    m_t = RevisionService.compute_recall(recall.forgetting_rate, elapsed)
                else:
                    m_t = 1.0
                group_a.append((book_rank, m_t, qid, round_row.round_num, round_row.lesson_id))
            for qid in skipped:
                group_b.append((book_rank, qid, round_row.round_num, round_row.lesson_id))

        # Group A blocks Tier 2 — serve weakest recall first, within selected book first
        if group_a:
            group_a.sort(key=lambda x: (x[0], x[1]))
            _, _, best_quiz_id, best_round_num, best_lesson_id = group_a[0]
            quiz_dict = _build_quiz_dict(db, best_quiz_id, best_round_num, best_lesson_id)
            return SlideResult(slide_type="quiz", chapter=None, quiz=quiz_dict)

        # Group B also blocks Tier 2 — oldest skip first, within selected book first
        if group_b:
            # Stable sort by book_rank preserves the existing oldest-skip-first order
            # inside each partition.
            group_b.sort(key=lambda x: x[0])
            _, best_quiz_id, best_round_num, best_lesson_id = group_b[0]
            quiz_dict = _build_quiz_dict(db, best_quiz_id, best_round_num, best_lesson_id)
            return SlideResult(slide_type="quiz", chapter=None, quiz=quiz_dict)

        # Tier 2: next unlearnt chapter (only when both Group A and Group B are empty)
        if book_id:
            chapter = get_next_chapter_in_book(db, username, book_id)
        else:
            chapters = get_next_chapters_all_books(db, username)
            chapter = random.choice(chapters) if chapters else None

        if chapter:
            chapter_dict = _build_chapter_dict(db, chapter)
            return SlideResult(slide_type="chapter", chapter=chapter_dict, quiz=None)

        return SlideResult(slide_type="none", chapter=None, quiz=None)
