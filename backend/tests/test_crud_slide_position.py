"""Tests for crud_slide_position CRUD functions."""

import pytest
from passlib.context import CryptContext

from src.crud.crud_slide_position import (
    clear_forward,
    get_history_depth,
    get_position,
    go_back,
    pop_from_forward,
    push_to_forward,
    push_to_history,
    save_feedback,
    save_position,
)
from src.crud.crud_user import create_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def user(db_session):  # pylint: disable=redefined-outer-name
    """Create a test user."""
    hashed = bcrypt_context.hash("pass")
    return create_user(db_session, "nav_user", hashed)


class TestSaveAndGetPosition:
    """Tests for save_position and get_position."""

    def test_save_and_get_position(self, db_session, user):  # pylint: disable=redefined-outer-name
        """Saving a position allows retrieval."""
        save_position(db_session, user.username, "chapter", 1, None, None)
        pos = get_position(db_session, user.username)
        assert pos is not None
        assert pos.slide_type == "chapter"
        assert pos.slide_id == 1

    def test_save_position_pushes_to_history(
        self, db_session, user
    ):  # pylint: disable=redefined-outer-name
        """Saving a second position pushes the first to back-history."""
        save_position(db_session, user.username, "chapter", 1, None, None)
        assert get_history_depth(db_session, user.username) == 0

        save_position(db_session, user.username, "quiz", 10, 5, 0)
        assert get_history_depth(db_session, user.username) == 1

        pos = get_position(db_session, user.username)
        assert pos.slide_type == "quiz"
        assert pos.slide_id == 10

    def test_save_feedback(self, db_session, user):  # pylint: disable=redefined-outer-name
        """save_feedback updates feedback_json on current position."""
        save_position(db_session, user.username, "quiz", 10, 5, 0)
        feedback = {"is_correct": True, "good_points": ["Good"], "bad_points": []}
        save_feedback(db_session, user.username, feedback)
        pos = get_position(db_session, user.username)
        assert pos.feedback_json == feedback

    def test_save_feedback_no_position(self, db_session, user):  # pylint: disable=redefined-outer-name
        """save_feedback is a no-op when no position exists."""
        save_feedback(db_session, user.username, {"is_correct": True})


class TestHistoryStack:
    """Tests for back-history stack operations."""

    def test_get_history_depth_empty(self, db_session, user):  # pylint: disable=redefined-outer-name
        """History depth is 0 for a new user."""
        assert get_history_depth(db_session, user.username) == 0

    def test_push_to_history_increments_depth(
        self, db_session, user
    ):  # pylint: disable=redefined-outer-name
        """push_to_history increases history depth."""
        push_to_history(db_session, user.username, "chapter", 1, None, None, None, "back")
        assert get_history_depth(db_session, user.username) == 1
        push_to_history(db_session, user.username, "chapter", 2, None, None, None, "back")
        assert get_history_depth(db_session, user.username) == 2

    def test_go_back_pops_history(self, db_session, user):  # pylint: disable=redefined-outer-name
        """go_back moves current to forward and restores previous slide."""
        save_position(db_session, user.username, "chapter", 1, None, None)
        save_position(db_session, user.username, "chapter", 2, None, None)

        assert get_history_depth(db_session, user.username) == 1
        prev = go_back(db_session, user.username)

        assert prev is not None
        assert prev.slide_id == 1
        assert get_history_depth(db_session, user.username) == 0

        pos = get_position(db_session, user.username)
        assert pos.slide_id == 1

    def test_go_back_no_history_returns_none(
        self, db_session, user
    ):  # pylint: disable=redefined-outer-name
        """go_back returns None when there is no history."""
        save_position(db_session, user.username, "chapter", 1, None, None)
        result = go_back(db_session, user.username)
        assert result is None


class TestForwardStack:
    """Tests for forward stack operations."""

    def test_push_pop_forward_stack(self, db_session, user):  # pylint: disable=redefined-outer-name
        """push_to_forward and pop_from_forward work correctly."""
        push_to_forward(db_session, user.username, "chapter", 5, None, None, None)
        fwd = pop_from_forward(db_session, user.username)
        assert fwd is not None
        assert fwd.slide_id == 5
        assert pop_from_forward(db_session, user.username) is None

    def test_clear_forward(self, db_session, user):  # pylint: disable=redefined-outer-name
        """clear_forward removes all forward entries."""
        push_to_forward(db_session, user.username, "chapter", 5, None, None, None)
        push_to_forward(db_session, user.username, "quiz", 10, 1, 0, None)
        clear_forward(db_session, user.username)
        assert pop_from_forward(db_session, user.username) is None

    def test_go_back_pushes_to_forward(
        self, db_session, user
    ):  # pylint: disable=redefined-outer-name
        """go_back pushes current slide to forward stack."""
        save_position(db_session, user.username, "chapter", 1, None, None)
        save_position(db_session, user.username, "chapter", 2, None, None)
        go_back(db_session, user.username)

        fwd = pop_from_forward(db_session, user.username)
        assert fwd is not None
        assert fwd.slide_id == 2
