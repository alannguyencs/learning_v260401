"""Tests for RevisionService: round creation, completion, and recall tracking."""

import math

import pytest
from passlib.context import CryptContext

from src.crud.crud_content import (
    create_book,
    create_chapter,
    create_chapter_quiz,
    create_lesson,
)
from src.crud.crud_learning_progress import mark_chapter_learnt
from src.crud.crud_revision import (
    complete_round,
    get_latest_round,
    get_open_round,
    get_quiz_recall,
)
from src.crud.crud_user import create_user
from src.service.revision_service import RevisionService

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def setup(db_session):  # pylint: disable=redefined-outer-name
    """Create a user, book, lesson, and chapters with quizzes."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "testuser", hashed)

    book = create_book(db_session, "ml", "Machine Learning")
    lesson = create_lesson(db_session, book.book_id, 1, "Intro")

    chapter1 = create_chapter(db_session, lesson.id, 1, "Ch1", "content1")
    chapter2 = create_chapter(db_session, lesson.id, 2, "Ch2", "content2")

    q1 = create_chapter_quiz(
        db_session,
        chapter1.id,
        "multiple_choice",
        "Q1?",
        None,
        "A",
        "B",
        "C",
        "D",
        ["A"],
    )
    q2 = create_chapter_quiz(
        db_session,
        chapter1.id,
        "multiple_choice",
        "Q2?",
        None,
        "A",
        "B",
        "C",
        "D",
        ["B"],
    )
    q3 = create_chapter_quiz(
        db_session,
        chapter2.id,
        "free_recall",
        "Q3?",
        "answer",
        None,
        None,
        None,
        None,
        None,
    )

    return {
        "db": db_session,
        "lesson": lesson,
        "chapter1": chapter1,
        "chapter2": chapter2,
        "quiz_ids_ch1": [q1.id, q2.id],
        "quiz_ids_ch2": [q3.id],
        "all_quiz_ids": [q1.id, q2.id, q3.id],
        "q1": q1,
        "q2": q2,
        "q3": q3,
    }


class TestOnChapterLearnt:
    """Tests for RevisionService.on_chapter_learnt."""

    def test_r0_created_on_first_chapter_learnt(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """R0 row created with due_at=lesson_count when no rounds exist."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, lesson_count=3)

        r0 = get_open_round(db, "testuser", lesson.id, 0)
        assert r0 is not None
        assert r0.due_at_lesson_count == 3
        assert r0.quizzes_in_round == 2
        assert r0.status == "open"

    def test_r0_quiz_count_grows_as_chapters_added(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Second chapter learnt increments R0's quizzes_in_round."""
        db = setup["db"]
        lesson = setup["lesson"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, setup["quiz_ids_ch1"], 1)
        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, setup["quiz_ids_ch2"], 2)

        r0 = get_open_round(db, "testuser", lesson.id, 0)
        assert r0.quizzes_in_round == 3

    def test_quizzes_added_to_r1_when_r0_done(self, setup):  # pylint: disable=redefined-outer-name
        """Late chapters go into R1 when R0 is already done."""
        db = setup["db"]
        lesson = setup["lesson"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, setup["quiz_ids_ch1"], 1)

        r0 = get_open_round(db, "testuser", lesson.id, 0)
        complete_round(db, r0.id, completed_at_lesson_count=2)

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, setup["quiz_ids_ch2"], 3)

        latest = get_latest_round(db, "testuser", lesson.id)
        assert latest.round_num == 1
        assert latest.quizzes_in_round == 1


class TestRecordQuizResponse:
    """Tests for RevisionService.record_quiz_response."""

    def test_quiz_answer_increments_answered_count(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Answering a quiz increments quizzes_answered."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, True, 1)

        r0 = get_open_round(db, "testuser", lesson.id, 0)
        assert r0.quizzes_answered == 1

    def test_skip_does_not_increment_answered(self, setup):  # pylint: disable=redefined-outer-name
        """Skip (is_correct=None) leaves quizzes_answered unchanged."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, None, 1)

        r0 = get_open_round(db, "testuser", lesson.id, 0)
        assert r0.quizzes_answered == 0

    def test_round_completes_at_50_percent(self, setup):  # pylint: disable=redefined-outer-name
        """Answering >50% of total lesson quizzes flips round status to done."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        # Mark all chapters learnt (required second condition)
        mark_chapter_learnt(db, "testuser", setup["chapter1"].id)
        mark_chapter_learnt(db, "testuser", setup["chapter2"].id)

        # 3 total lesson quizzes — answer 2 → 66% > 50%, all chapters learnt
        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, True, 1)
        result = RevisionService.record_quiz_response(
            db, "testuser", quiz_ids[1], lesson.id, 0, True, 1
        )

        assert result.round_done is True

    def test_round_does_not_complete_without_all_chapters_learnt(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """R0 stays open when >50% answered but not all chapters are learnt."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        # Only chapter1 learnt — chapter2 still pending
        mark_chapter_learnt(db, "testuser", setup["chapter1"].id)

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, True, 1)
        result = RevisionService.record_quiz_response(
            db, "testuser", quiz_ids[1], lesson.id, 0, True, 1
        )

        assert result.round_done is False

    def test_next_round_created_after_completion(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """R1 created with due_at = lesson_count + 2^(0+1) = lesson_count + 2."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        # Mark all chapters learnt (required second condition)
        mark_chapter_learnt(db, "testuser", setup["chapter1"].id)
        mark_chapter_learnt(db, "testuser", setup["chapter2"].id)

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, True, 5)
        result = RevisionService.record_quiz_response(
            db, "testuser", quiz_ids[1], lesson.id, 0, True, 5
        )

        assert result.round_done is True
        assert result.next_round_num == 1
        assert result.next_round_due_at == 5 + 2  # 2^(0+1) = 2


class TestMemorize:
    """Tests for MEMORIZE forgetting rate updates."""

    def test_memorize_correct_reduces_forgetting_rate(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Correct answer multiplies forgetting_rate by 0.7."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, True, 1)

        recall = get_quiz_recall(db, "testuser", quiz_ids[0])
        assert abs(recall.forgetting_rate - 0.7) < 1e-9

    def test_memorize_incorrect_increases_forgetting_rate(
        self, setup
    ):  # pylint: disable=redefined-outer-name
        """Incorrect answer multiplies forgetting_rate by 1.2."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        RevisionService.record_quiz_response(db, "testuser", quiz_ids[0], lesson.id, 0, False, 1)

        recall = get_quiz_recall(db, "testuser", quiz_ids[0])
        assert abs(recall.forgetting_rate - 1.2) < 1e-9

    def test_memorize_forgetting_rate_capped(self, setup):  # pylint: disable=redefined-outer-name
        """forgetting_rate never exceeds 1.5."""
        db = setup["db"]
        lesson = setup["lesson"]
        quiz_ids = setup["quiz_ids_ch1"]

        RevisionService.on_chapter_learnt(db, "testuser", lesson.id, quiz_ids, 1)
        # Answer wrong several times to push rate past 1.5
        for _ in range(10):
            RevisionService.record_quiz_response(
                db, "testuser", quiz_ids[0], lesson.id, 0, False, 1
            )

        recall = get_quiz_recall(db, "testuser", quiz_ids[0])
        assert recall.forgetting_rate <= 1.5

    def test_recall_score_formula(self):
        """compute_recall returns exp(-rate * elapsed / 10)."""
        rate = 0.7
        elapsed = 5
        expected = math.exp(-rate * elapsed / 10)
        assert abs(RevisionService.compute_recall(rate, elapsed) - expected) < 1e-9
