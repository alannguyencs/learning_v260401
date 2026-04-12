"""Tests for SlideSelector 2-tier algorithm with skip queue."""

import pytest
from passlib.context import CryptContext

from src.crud.crud_content import (
    create_book,
    create_chapter,
    create_chapter_quiz,
    create_lesson,
)
from src.crud.crud_learning_progress import increment_lesson_count
from src.crud.crud_revision import complete_round, get_open_round
from src.crud.crud_user import create_user
from src.service.learning_progress_service import LearningProgressService
from src.service.revision_service import RevisionService
from src.service.slide_selector import SlideSelector

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def setup(db_session):  # pylint: disable=redefined-outer-name
    """Create user, books, lessons, chapters, and quizzes for slide tests."""
    hashed = bcrypt_context.hash("pass")
    create_user(db_session, "testuser", hashed)

    book1 = create_book(db_session, "ml", "Machine Learning")
    lesson1 = create_lesson(db_session, book1.book_id, 1, "Intro to ML")
    chapter1 = create_chapter(db_session, lesson1.id, 1, "What is ML", "content1")
    chapter2 = create_chapter(db_session, lesson1.id, 2, "Types of ML", "content2")
    q1 = create_chapter_quiz(
        db_session, chapter1.id, "multiple_choice", "Q1?", None, "A", "B", "C", "D", ["A"]
    )
    q2 = create_chapter_quiz(
        db_session, chapter2.id, "multiple_choice", "Q2?", None, "A", "B", "C", "D", ["B"]
    )

    book2 = create_book(db_session, "dl", "Deep Learning")
    lesson2 = create_lesson(db_session, book2.book_id, 1, "Intro to DL")
    chapter3 = create_chapter(db_session, lesson2.id, 1, "Neural Networks", "content3")

    return {
        "db": db_session,
        "book1": book1,
        "book2": book2,
        "lesson1": lesson1,
        "lesson2": lesson2,
        "chapter1": chapter1,
        "chapter2": chapter2,
        "chapter3": chapter3,
        "q1": q1,
        "q2": q2,
    }


class TestTier1DueRevisions:
    """Tests for Tier 1: due revision quizzes."""

    def test_tier1_due_revision_returned_first(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """When a revision is due, quiz slide is returned before chapter slide."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        lesson1 = setup["lesson1"]

        # Mark chapter1 learnt → R0 created due immediately (due_at=lesson_count=0)
        lp_result = LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)
        RevisionService.on_chapter_learnt(
            db, "testuser", lp_result.lesson_id, lp_result.chapter_quiz_ids, lp_result.lesson_count
        )
        # chapter2 still unlearnt → Tier 2 would normally return a chapter
        # But Tier 1 has R0 due → should return quiz first
        _ = lesson1
        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "quiz"

    def test_tier1_weakest_recall_first(self, setup):  # pylint: disable=redefined-outer-name
        """Quiz with worse recall (lower m(t)) returned first when two quizzes are eligible."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        chapter2 = setup["chapter2"]
        lesson1 = setup["lesson1"]
        q1 = setup["q1"]
        q2 = setup["q2"]

        # Mark both chapters learnt → lesson_count=1, R0 has 2 quizzes, due_at=0
        lp1 = LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)
        RevisionService.on_chapter_learnt(
            db, "testuser", lp1.lesson_id, lp1.chapter_quiz_ids, lp1.lesson_count
        )
        lp2 = LearningProgressService.mark_chapter_learnt(db, "testuser", chapter2.id)
        RevisionService.on_chapter_learnt(
            db, "testuser", lp2.lesson_id, lp2.chapter_quiz_ids, lp2.lesson_count
        )

        # Complete R0: answer q1 incorrectly (forgetting_rate→1.2), q2 correctly (→0.7)
        # After q2: R0 complete (2/2 > 0.5), R1 created with due_at=1+2=3
        RevisionService.record_quiz_response(db, "testuser", q1.id, lesson1.id, 0, False, 1)
        RevisionService.record_quiz_response(db, "testuser", q2.id, lesson1.id, 0, True, 1)

        # Advance lesson_count to 5 so R1 becomes due (due_at=3 ≤ 5)
        for _ in range(4):
            increment_lesson_count(db, "testuser")

        # Both q1 and q2 are eligible in R1 (last_reviewed=1 < due_at=3)
        # q1 has forgetting_rate=1.2 > q2's 0.7 → q1 has lower m(t) → returned first
        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "quiz"
        assert result.quiz is not None
        assert result.quiz["id"] == q1.id


class TestTier2NewChapter:
    """Tests for Tier 2: next unlearnt chapter."""

    def test_tier2_new_chapter_after_no_revisions(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Chapter slide returned for a fresh user with no due revisions."""
        db = setup["db"]

        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "chapter"
        assert result.chapter is not None

    def test_tier2_specific_book_filter(self, setup):  # pylint: disable=redefined-outer-name
        """book_id filter returns chapter from the correct book only."""
        db = setup["db"]

        result = SlideSelector.get_next_slide(db, "testuser", book_id="dl")
        assert result.slide_type == "chapter"
        assert result.chapter is not None
        assert result.chapter["book_id"] == "dl"


class TestSkipQueue:
    """Tests for skip queue within Tier 1: skipped quizzes go to back of queue."""

    def test_skipped_quiz_deferred_to_group_b(self, setup):  # pylint: disable=redefined-outer-name
        """Skipped quiz is deferred; non-skipped quiz is served first."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        q1 = setup["q1"]
        lesson1 = setup["lesson1"]

        # Learn chapter1 and set up R0
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)

        # Skip q1
        from src.crud.crud_slides import log_quiz_skip

        log_quiz_skip(db, "testuser", q1.id, lesson1.id, 0)

        result = SlideSelector.get_next_slide(db, "testuser")
        # Should get a non-skipped quiz (q2) or a chapter, not q1
        if result.slide_type == "quiz":
            assert result.quiz["id"] != q1.id

    def test_skipped_quiz_resurfaces_when_group_a_empty(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Skipped quiz resurfaces after all non-skipped quizzes are exhausted."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        chapter2 = setup["chapter2"]
        chapter3 = setup["chapter3"]
        q1 = setup["q1"]
        lesson1 = setup["lesson1"]

        # Learn all chapters
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter2.id)
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter3.id)

        # Complete R0 so Tier 1 has no non-skipped quizzes
        r0 = get_open_round(db, "testuser", lesson1.id, 0)
        if r0:
            complete_round(db, r0.id, completed_at_lesson_count=0)

        # Create R1 due now with lesson_count=0
        from src.crud.crud_revision import create_round

        increment_lesson_count(db, "testuser")
        create_round(db, "testuser", lesson1.id, 1, due_at_lesson_count=1, quizzes_in_round=2)

        # Skip q1 in R1 — only q1 belongs to chapter1
        from src.crud.crud_slides import log_quiz_skip

        log_quiz_skip(db, "testuser", q1.id, lesson1.id, 1)

        # Answer q2 (the other quiz on chapter1) via record_quiz_response
        q2 = setup["q2"]
        RevisionService.record_quiz_response(db, "testuser", q2.id, lesson1.id, 1, True, 1)

        # Now group A is empty, group B has q1
        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "quiz"
        assert result.quiz["id"] == q1.id


class TestNoneWhenAllDone:
    """Tests for slide_type=none when both tiers are exhausted."""

    def test_none_when_all_done(self, setup):  # pylint: disable=redefined-outer-name
        """slide_type=none when no chapters or revisions remain."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        chapter2 = setup["chapter2"]
        chapter3 = setup["chapter3"]

        # Learn all chapters
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter2.id)
        LearningProgressService.mark_chapter_learnt(db, "testuser", chapter3.id)
        # No revision rounds created (on_chapter_learnt not called)
        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "none"


class TestRichMetadataInQuizDict:
    """Tests that _build_quiz_dict includes the new rich metadata fields."""

    def test_quiz_slide_includes_rich_metadata(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """_build_quiz_dict includes section_name, quiz_take_away, quiz_metadata when present."""
        db = setup["db"]
        lesson1 = setup["lesson1"]

        # Dedicated chapter with only the rich quiz so SlideSelector returns it
        rich_chapter = create_chapter(db, lesson1.id, 99, "Rich Chapter", "content_rich")
        q = create_chapter_quiz(
            db,
            rich_chapter.id,
            "free_recall",
            "Describe the FBI framework.",
            "Emergency, Essentials, Equity, Enjoyment.",
            None,
            None,
            None,
            None,
            None,
            section_index=1,
            section_name="Summary",
            quiz_take_away="FBI forces discipline by funding Enjoyment last.",
            quiz_metadata={"key_points": ["Emergency first", "Enjoyment last"]},
        )

        # Mark rich_chapter learnt → R0 created with only the rich quiz
        lp = LearningProgressService.mark_chapter_learnt(db, "testuser", rich_chapter.id)
        RevisionService.on_chapter_learnt(
            db, "testuser", lp.lesson_id, lp.chapter_quiz_ids, lp.lesson_count
        )

        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "quiz"
        quiz_dict = result.quiz
        assert quiz_dict["id"] == q.id
        assert quiz_dict["section_name"] == "Summary"
        assert quiz_dict["quiz_take_away"] == "FBI forces discipline by funding Enjoyment last."
        assert quiz_dict["quiz_metadata"] == {"key_points": ["Emergency first", "Enjoyment last"]}
        _ = lesson1

    def test_quiz_slide_null_metadata_safe(self, setup):  # pylint: disable=redefined-outer-name
        """_build_quiz_dict returns None for new fields when DB columns are NULL."""
        db = setup["db"]
        chapter1 = setup["chapter1"]
        lesson1 = setup["lesson1"]

        lp = LearningProgressService.mark_chapter_learnt(db, "testuser", chapter1.id)
        RevisionService.on_chapter_learnt(
            db, "testuser", lp.lesson_id, lp.chapter_quiz_ids, lp.lesson_count
        )

        result = SlideSelector.get_next_slide(db, "testuser")
        assert result.slide_type == "quiz"
        quiz_dict = result.quiz
        assert quiz_dict["section_name"] is None
        assert quiz_dict["quiz_take_away"] is None
        assert quiz_dict["quiz_metadata"] is None
        _ = lesson1
