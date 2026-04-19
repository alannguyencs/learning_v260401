"""Tests for user_slide_like CRUD operations."""

# pylint: disable=redefined-outer-name

import pytest
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from src.crud.crud_content import (
    create_book,
    create_chapter,
    create_chapter_quiz,
    create_lesson,
)
from src.crud.crud_slide_like import (
    add_chapter_like,
    add_like,
    get_liked_chapter_ids,
    get_liked_items_with_context,
    get_liked_quiz_ids,
    is_chapter_liked,
    is_liked,
    remove_chapter_like,
    remove_like,
)
from src.crud.crud_user import create_user
from src.models.slide_like import UserSlideLike

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

    def test_get_liked_quiz_ids_orders_newest_first(self, db_session, setup_user_and_quiz):
        """Liked IDs are returned newest-first."""
        username, quiz_a, quiz_b = setup_user_and_quiz
        add_like(db_session, username, quiz_a)
        add_like(db_session, username, quiz_b)
        ids = get_liked_quiz_ids(db_session, username)
        assert set(ids) == {quiz_a, quiz_b}
        assert ids[0] == quiz_b


@pytest.fixture()
def setup_user_quiz_and_chapter(db_session):
    """Create a user, two chapters, and a quiz for polymorphic-like tests."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "polyuser", hashed)
    create_book(db_session, "bk2", "Book 2")
    lesson = create_lesson(db_session, "bk2", 1, "Lesson")
    chapter_a = create_chapter(db_session, lesson.id, 1, "Ch A", "body-a")
    chapter_b = create_chapter(db_session, lesson.id, 2, "Ch B", "body-b")
    quiz_id = _make_quiz(db_session, chapter_a.id, "A")
    return "polyuser", quiz_id, chapter_a.id, chapter_b.id


class TestCrudChapterLike:
    """Tests for the chapter-like leg of crud_slide_like."""

    def test_add_chapter_like_inserts_row(self, db_session, setup_user_quiz_and_chapter):
        """add_chapter_like inserts a chapter-only row."""
        username, _, chapter_id, _ = setup_user_quiz_and_chapter
        assert is_chapter_liked(db_session, username, chapter_id) is False
        add_chapter_like(db_session, username, chapter_id)
        assert is_chapter_liked(db_session, username, chapter_id) is True
        # The row has chapter_id set and quiz_id null
        row = (
            db_session.query(UserSlideLike)
            .filter(
                UserSlideLike.username == username,
                UserSlideLike.chapter_id == chapter_id,
            )
            .first()
        )
        assert row is not None
        assert row.quiz_id is None
        assert row.chapter_id == chapter_id

    def test_add_chapter_like_is_idempotent(self, db_session, setup_user_quiz_and_chapter):
        """Two add_chapter_like calls yield a single row."""
        username, _, chapter_id, _ = setup_user_quiz_and_chapter
        add_chapter_like(db_session, username, chapter_id)
        add_chapter_like(db_session, username, chapter_id)
        assert get_liked_chapter_ids(db_session, username) == [chapter_id]

    def test_remove_chapter_like_deletes_row(self, db_session, setup_user_quiz_and_chapter):
        """remove_chapter_like clears the row."""
        username, _, chapter_id, _ = setup_user_quiz_and_chapter
        add_chapter_like(db_session, username, chapter_id)
        remove_chapter_like(db_session, username, chapter_id)
        assert is_chapter_liked(db_session, username, chapter_id) is False

    def test_remove_chapter_like_is_idempotent(self, db_session, setup_user_quiz_and_chapter):
        """remove_chapter_like on an absent row is a no-op."""
        username, _, chapter_id, _ = setup_user_quiz_and_chapter
        remove_chapter_like(db_session, username, chapter_id)
        remove_chapter_like(db_session, username, chapter_id)
        assert is_chapter_liked(db_session, username, chapter_id) is False

    def test_get_liked_chapter_ids_orders_newest_first(
        self, db_session, setup_user_quiz_and_chapter
    ):
        """Liked chapter IDs are returned newest-first."""
        username, _, chapter_a, chapter_b = setup_user_quiz_and_chapter
        add_chapter_like(db_session, username, chapter_a)
        add_chapter_like(db_session, username, chapter_b)
        ids = get_liked_chapter_ids(db_session, username)
        assert set(ids) == {chapter_a, chapter_b}
        assert ids[0] == chapter_b

    def test_quiz_helpers_ignore_chapter_rows(self, db_session, setup_user_quiz_and_chapter):
        """get_liked_quiz_ids must not return chapter-only rows."""
        username, quiz_id, chapter_id, _ = setup_user_quiz_and_chapter
        add_like(db_session, username, quiz_id)
        add_chapter_like(db_session, username, chapter_id)
        quiz_ids = get_liked_quiz_ids(db_session, username)
        chapter_ids = get_liked_chapter_ids(db_session, username)
        assert quiz_ids == [quiz_id]
        assert chapter_ids == [chapter_id]

    def test_get_liked_items_with_context_interleaves(
        self, db_session, setup_user_quiz_and_chapter
    ):
        """get_liked_items_with_context returns mixed rows, newest first."""
        username, quiz_id, chapter_id, _ = setup_user_quiz_and_chapter
        add_chapter_like(db_session, username, chapter_id)
        add_like(db_session, username, quiz_id)
        items = get_liked_items_with_context(db_session, username)
        assert len(items) == 2
        # Most recent like (quiz) is first
        assert items[0].kind == "quiz"
        assert items[0].quiz is not None
        assert items[0].quiz.id == quiz_id
        assert items[1].kind == "chapter"
        assert items[1].chapter is not None
        assert items[1].chapter.id == chapter_id


class TestUserSlideLikeCheckConstraint:
    """Verify the DB-level CHECK constraint enforces exactly-one target."""

    def test_both_null_raises(self, db_session, setup_user_quiz_and_chapter):
        """A row with neither quiz_id nor chapter_id set violates the CHECK."""
        username, _, _, _ = setup_user_quiz_and_chapter
        db_session.add(UserSlideLike(username=username, quiz_id=None, chapter_id=None))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_both_set_raises(self, db_session, setup_user_quiz_and_chapter):
        """A row with both quiz_id and chapter_id set violates the CHECK."""
        username, quiz_id, chapter_id, _ = setup_user_quiz_and_chapter
        db_session.add(UserSlideLike(username=username, quiz_id=quiz_id, chapter_id=chapter_id))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
