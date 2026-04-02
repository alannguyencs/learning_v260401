"""Tests for slide chat CRUD operations."""

import pytest
from passlib.context import CryptContext

from src.crud.crud_slide_chat import get_chat_messages, get_recent_chat_messages, save_chat_message
from src.crud.crud_user import create_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def setup_user(db_session):
    """Create a test user."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "chatuser", hashed)
    return "chatuser"


class TestSlideChatCrud:
    """Tests for slide chat CRUD functions."""

    def test_save_chat_message(self, db_session, setup_user):
        """save_chat_message inserts correctly."""
        msg = save_chat_message(db_session, setup_user, "chapter:1", "user", "Hello")
        assert msg.id is not None
        assert msg.username == setup_user
        assert msg.slide_identifier == "chapter:1"
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_get_chat_messages_ordered(self, db_session, setup_user):
        """get_chat_messages returns all messages ordered ASC."""
        save_chat_message(db_session, setup_user, "chapter:1", "user", "Q1")
        save_chat_message(db_session, setup_user, "chapter:1", "assistant", "A1")
        save_chat_message(db_session, setup_user, "chapter:1", "user", "Q2")

        msgs = get_chat_messages(db_session, setup_user, "chapter:1")
        assert len(msgs) == 3
        assert msgs[0].content == "Q1"
        assert msgs[1].content == "A1"
        assert msgs[2].content == "Q2"

    def test_get_recent_chat_messages_limits(self, db_session, setup_user):
        """get_recent_chat_messages returns only last N messages."""
        for i in range(5):
            save_chat_message(db_session, setup_user, "quiz:1", "user", f"Q{i}")

        recent = get_recent_chat_messages(db_session, setup_user, "quiz:1", limit=3)
        assert len(recent) == 3
        assert recent[0].content == "Q2"
        assert recent[2].content == "Q4"

    def test_get_chat_messages_filters_by_slide(self, db_session, setup_user):
        """Messages from different slides are not mixed."""
        save_chat_message(db_session, setup_user, "chapter:1", "user", "Ch1 msg")
        save_chat_message(db_session, setup_user, "chapter:2", "user", "Ch2 msg")

        msgs = get_chat_messages(db_session, setup_user, "chapter:1")
        assert len(msgs) == 1
        assert msgs[0].content == "Ch1 msg"
