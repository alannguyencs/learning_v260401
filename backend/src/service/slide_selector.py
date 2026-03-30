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
    get_skipped_quizzes,
)
from src.models.content import Book, Chapter, Lesson
from src.service.revision_service import RevisionService


@dataclass
class SlideResult:
    """Result of the slide selection algorithm."""

    slide_type: str  # 'chapter', 'quiz', or 'none'
    chapter: Optional[dict]
    quiz: Optional[dict]


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
    }


class SlideSelector:
    """Implements the 3-tier slide priority algorithm from spec §7.4."""

    @staticmethod
    def get_next_slide(
        db: Session, username: str, book_id: Optional[str] = None
    ) -> SlideResult:
        """
        Return the next slide for the user.

        Priority:
        1. Due revision quizzes (weakest recall first)
        2. Next unlearnt chapter
        3. Skipped quizzes (oldest first)
        """
        lesson_count = crud_learning_progress.get_lesson_count(db, username)

        # Tier 1: due revision quizzes
        due_rounds = get_due_rounds(db, username, lesson_count)
        quiz_candidates = []

        for round_row in due_rounds:
            eligible_ids = get_eligible_quiz_ids_for_round(
                db, username, round_row.lesson_id, round_row.round_num
            )
            for qid in eligible_ids:
                recall = get_quiz_recall(db, username, qid)
                if recall is not None:
                    last_reviewed = recall.last_reviewed_lesson_count or 0
                    elapsed = lesson_count - last_reviewed
                    m_t = RevisionService.compute_recall(recall.forgetting_rate, elapsed)
                else:
                    m_t = 1.0
                quiz_candidates.append((m_t, qid, round_row.round_num, round_row.lesson_id))

        if quiz_candidates:
            quiz_candidates.sort(key=lambda x: x[0])
            _, best_quiz_id, best_round_num, best_lesson_id = quiz_candidates[0]
            quiz_dict = _build_quiz_dict(db, best_quiz_id, best_round_num, best_lesson_id)
            return SlideResult(slide_type="quiz", chapter=None, quiz=quiz_dict)

        # Tier 2: next unlearnt chapter
        if book_id:
            chapter = get_next_chapter_in_book(db, username, book_id)
        else:
            chapters = get_next_chapters_all_books(db, username)
            chapter = random.choice(chapters) if chapters else None

        if chapter:
            chapter_dict = _build_chapter_dict(db, chapter)
            return SlideResult(slide_type="chapter", chapter=chapter_dict, quiz=None)

        # Tier 3: skipped quizzes
        skipped = get_skipped_quizzes(db, username)
        if skipped:
            first = skipped[0]
            quiz_dict = _build_quiz_dict(db, first["quiz_id"], first["round_num"], first["lesson_id"])
            return SlideResult(slide_type="quiz", chapter=None, quiz=quiz_dict)

        return SlideResult(slide_type="none", chapter=None, quiz=None)
