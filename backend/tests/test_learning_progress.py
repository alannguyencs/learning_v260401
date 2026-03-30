"""Tests for LearningProgressService and crud_learning_progress."""

from src.crud.crud_content import create_book, create_chapter, create_lesson
from src.crud.crud_user import create_user
from src.service.learning_progress_service import LearningProgressService

from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _seed_user(db, username="testuser"):
    """Create a test user."""
    hashed = bcrypt_context.hash("testpass")
    return create_user(db, username, hashed)


def _seed_lesson_with_chapters(db, num_chapters=2):
    """Create a book, one lesson, and the given number of chapters. Return chapter ids."""
    create_book(db, book_id="test_book", title="Test Book")
    lesson = create_lesson(db, book_id="test_book", lesson_index=1, title="Lesson 1")
    chapter_ids = []
    for i in range(1, num_chapters + 1):
        chapter = create_chapter(
            db,
            lesson_id=lesson.id,
            chapter_index=i,
            title=f"Chapter {i}",
            content=f"# Chapter {i}",
        )
        chapter_ids.append(chapter.id)
    return lesson.id, chapter_ids


class TestMarkChapterLearnt:
    """Tests for LearningProgressService.mark_chapter_learnt."""

    def test_mark_chapter_learnt_first_time(self, db_session):
        """Marking a chapter creates a progress row and returns lesson_fully_learnt=False (2 chapters)."""
        _seed_user(db_session)
        lesson_id, chapter_ids = _seed_lesson_with_chapters(db_session, num_chapters=2)

        result = LearningProgressService.mark_chapter_learnt(
            db_session, "testuser", chapter_ids[0]
        )

        assert result.lesson_id == lesson_id
        assert result.lesson_fully_learnt is False
        assert result.lesson_count == 0

    def test_mark_chapter_learnt_idempotent(self, db_session):
        """Marking the same chapter twice doesn't create a duplicate or error."""
        _seed_user(db_session)
        _lesson_id, chapter_ids = _seed_lesson_with_chapters(db_session, num_chapters=2)

        LearningProgressService.mark_chapter_learnt(db_session, "testuser", chapter_ids[0])
        result = LearningProgressService.mark_chapter_learnt(
            db_session, "testuser", chapter_ids[0]
        )

        assert result.lesson_fully_learnt is False
        assert result.lesson_count == 0

    def test_lesson_fully_learnt_detected(self, db_session):
        """After all chapters in a lesson are marked, lesson_fully_learnt=True."""
        _seed_user(db_session)
        _lesson_id, chapter_ids = _seed_lesson_with_chapters(db_session, num_chapters=2)

        LearningProgressService.mark_chapter_learnt(db_session, "testuser", chapter_ids[0])
        result = LearningProgressService.mark_chapter_learnt(
            db_session, "testuser", chapter_ids[1]
        )

        assert result.lesson_fully_learnt is True

    def test_lesson_count_increments_on_fully_learnt(self, db_session):
        """Completing all chapters of a lesson increments lesson_count from 0 to 1."""
        _seed_user(db_session)
        _lesson_id, chapter_ids = _seed_lesson_with_chapters(db_session, num_chapters=2)

        LearningProgressService.mark_chapter_learnt(db_session, "testuser", chapter_ids[0])
        result = LearningProgressService.mark_chapter_learnt(
            db_session, "testuser", chapter_ids[1]
        )

        assert result.lesson_count == 1

    def test_lesson_count_not_incremented_partial(self, db_session):
        """Partial completion (1 of 2 chapters) does not increment lesson_count."""
        _seed_user(db_session)
        _lesson_id, chapter_ids = _seed_lesson_with_chapters(db_session, num_chapters=2)

        result = LearningProgressService.mark_chapter_learnt(
            db_session, "testuser", chapter_ids[0]
        )

        assert result.lesson_count == 0

    def test_multiple_lessons_count(self, db_session):
        """Completing 2 separate lessons yields lesson_count=2."""
        _seed_user(db_session)
        create_book(db_session, book_id="book2", title="Book 2")

        lesson1 = create_lesson(db_session, book_id="test_book", lesson_index=1, title="L1")
        create_book(db_session, book_id="test_book", title="Test Book")
        lesson2 = create_lesson(db_session, book_id="book2", lesson_index=1, title="L2")

        ch1 = create_chapter(
            db_session, lesson_id=lesson1.id, chapter_index=1, title="C1", content="c1"
        )
        ch2 = create_chapter(
            db_session, lesson_id=lesson2.id, chapter_index=1, title="C2", content="c2"
        )

        LearningProgressService.mark_chapter_learnt(db_session, "testuser", ch1.id)
        result = LearningProgressService.mark_chapter_learnt(db_session, "testuser", ch2.id)

        assert result.lesson_count == 2
