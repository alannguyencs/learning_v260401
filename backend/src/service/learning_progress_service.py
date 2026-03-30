"""LearningProgressService: encapsulates chapter-learnt and lesson-count logic."""

from dataclasses import dataclass, field
from typing import List

from sqlalchemy.orm import Session

from src.crud import crud_learning_progress
from src.crud.crud_content import get_chapter, get_lesson_chapter_count, list_quizzes_for_chapter


@dataclass
class ChapterLearntResult:
    """Result of marking a chapter as learnt."""

    lesson_id: int
    lesson_fully_learnt: bool
    lesson_count: int
    chapter_quiz_ids: List[int] = field(default_factory=list)


class LearningProgressService:
    """Service for tracking chapter-learnt state and lesson count."""

    @staticmethod
    def mark_chapter_learnt(db: Session, username: str, chapter_id: int) -> ChapterLearntResult:
        """
        Mark a chapter as learnt and update the lesson count if the lesson is now complete.

        Steps:
        1. Record the chapter as learnt (idempotent).
        2. Retrieve the chapter's lesson_id and the total chapter count for the lesson.
        3. Count how many chapters in that lesson the user has now learnt.
        4. If all chapters are learnt, increment the user's lesson count.
        5. Return ChapterLearntResult with lesson_id, lesson_fully_learnt, lesson_count,
           and the chapter's quiz IDs (for revision scheduling).
        """
        crud_learning_progress.mark_chapter_learnt(db, username, chapter_id)

        chapter = get_chapter(db, chapter_id)
        lesson_id = chapter.lesson_id

        total_chapters = get_lesson_chapter_count(db, lesson_id)
        learnt_chapters = crud_learning_progress.count_learnt_chapters_in_lesson(
            db, username, lesson_id
        )

        lesson_fully_learnt = learnt_chapters == total_chapters

        if lesson_fully_learnt:
            lesson_count = crud_learning_progress.increment_lesson_count(db, username)
        else:
            lesson_count = crud_learning_progress.get_lesson_count(db, username)

        quiz_ids = [q.id for q in list_quizzes_for_chapter(db, chapter_id)]

        return ChapterLearntResult(
            lesson_id=lesson_id,
            lesson_fully_learnt=lesson_fully_learnt,
            lesson_count=lesson_count,
            chapter_quiz_ids=quiz_ids,
        )
