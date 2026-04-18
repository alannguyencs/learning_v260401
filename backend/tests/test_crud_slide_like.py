"""Tests for user_slide_like CRUD operations."""

# pylint: disable=redefined-outer-name

import pytest
from passlib.context import CryptContext

from src.crud.crud_content import (
    create_book,
    create_chapter,
    create_chapter_quiz,
    create_lesson,
)
from src.crud.crud_slide_like import (
    add_like,
    get_liked_quiz_ids,
    is_liked,
    remove_like,
)
from src.crud.crud_user import create_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _make_quiz(db, chapter_id, correct_letter):
    """Create a minimal MC quiz and return its id."""
    quiz = create_chapter_quiz(
        db,
        chapter_id=chapter_id,
        quiz_type="multiple_choice",
        question=f"q-{correct_letter}?",
        expected_answer=None,
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_options=[correct_letter],
    )
    return quiz.id


@pytest.fixture()
def setup_user_and_quiz(db_session):
    """Create a test user and two quizzes to like."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "likeuser", hashed)
    create_book(db_session, "bk1", "Book 1")
    lesson = create_lesson(db_session, "bk1", 1, "L1")
    chapter = create_chapter(db_session, lesson.id, 1, "C1", "x")
    quiz_a = _make_quiz(db_session, chapter.id, "A")
    quiz_b = _make_quiz(db_session, chapter.id, "B")
    return "likeuser", quiz_a, quiz_b


class TestCrudSlideLike:
    """Tests for crud_slide_like functions."""

    def test_add_like_inserts_row(self, db_session, setup_user_and_quiz):
        """add_like inserts a row visible to is_liked."""
        username, quiz_id, _ = setup_user_and_quiz
        assert is_liked(db_session, username, quiz_id) is False
        add_like(db_session, username, quiz_id)
        assert is_liked(db_session, username, quiz_id) is True

    def test_add_like_is_idempotent(self, db_session, setup_user_and_quiz):
        """Calling add_like twice does not raise and still yields one row."""
        username, quiz_id, _ = setup_user_and_quiz
        add_like(db_session, username, quiz_id)
        add_like(db_session, username, quiz_id)
        assert get_liked_quiz_ids(db_session, username) == [quiz_id]

    def test_remove_like_deletes_row(self, db_session, setup_user_and_quiz):
        """remove_like deletes the row and unsets is_liked."""
        username, quiz_id, _ = setup_user_and_quiz
        add_like(db_session, username, quiz_id)
        remove_like(db_session, username, quiz_id)
        assert is_liked(db_session, username, quiz_id) is False

    def test_remove_like_is_idempotent(self, db_session, setup_user_and_quiz):
        """remove_like on an absent row is a no-op."""
        username, quiz_id, _ = setup_user_and_quiz
        remove_like(db_session, username, quiz_id)
        remove_like(db_session, username, quiz_id)
        assert is_liked(db_session, username, quiz_id) is False

    def test_get_liked_quiz_ids_orders_newest_first(
        self, db_session, setup_user_and_quiz
    ):
        """Liked IDs are returned newest-first."""
        username, quiz_a, quiz_b = setup_user_and_quiz
        add_like(db_session, username, quiz_a)
        add_like(db_session, username, quiz_b)
        ids = get_liked_quiz_ids(db_session, username)
        assert set(ids) == {quiz_a, quiz_b}
        assert ids[0] == quiz_b
