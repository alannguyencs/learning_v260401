"""Tests for slide chat API endpoints."""

# pylint: disable=redefined-outer-name

from unittest.mock import MagicMock, patch

import pytest
from passlib.context import CryptContext

from src.configs import settings
from src.crud.crud_user import create_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_TOKEN = "test-agent-token"
BEARER_HEADER = {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest.fixture(autouse=True)
def set_agent_token(monkeypatch):
    """Override webapp_access_token for all tests in this module."""
    monkeypatch.setattr(settings, "webapp_access_token", TEST_TOKEN)


@pytest.fixture()
def auth_client(client, db_session):
    """Client with a logged-in session user."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "testuser", hashed)
    client.post("/api/login/", json={"username": "testuser", "password": "testpass"})
    return client


def _seed_content(client):
    """Create book/lesson/chapter with quiz; return ids."""
    client.post(
        "/api/content/books",
        json={"book_id": "ml", "title": "Machine Learning"},
        headers=BEARER_HEADER,
    )
    lesson_resp = client.post(
        "/api/content/lessons",
        json={"book_id": "ml", "lesson_index": 1, "title": "Intro", "raw_content": "Full text."},
        headers=BEARER_HEADER,
    )
    lesson_id = lesson_resp.json()["id"]
    chapter_resp = client.post(
        "/api/content/chapters",
        json={"lesson_id": lesson_id, "chapter_index": 1, "title": "Ch1", "content": "# Ch1"},
        headers=BEARER_HEADER,
    )
    chapter_id = chapter_resp.json()["id"]
    client.post(
        "/api/content/quizzes",
        json={
            "chapter_id": chapter_id,
            "quizzes": [
                {
                    "quiz_type": "free_recall",
                    "question": "What is ML?",
                    "expected_answer": "Machine Learning",
                }
            ],
        },
        headers=BEARER_HEADER,
    )
    return {"lesson_id": lesson_id, "chapter_id": chapter_id, "quiz_id": 1}


class TestSlideChatPost:
    """Tests for POST /api/slides/chat."""

    @patch("src.service.slide_chat_service.genai.Client")
    def test_chat_chapter_returns_response(self, mock_cls, auth_client):
        """POST chat with chapter slide returns AI response."""
        ids = _seed_content(auth_client)
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Neural networks are cool."
        mock_client.models.generate_content.return_value = mock_response

        resp = auth_client.post(
            "/api/slides/chat",
            json={
                "slide_type": "chapter",
                "chapter_id": ids["chapter_id"],
                "message": "What is this about?",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["response"] == "Neural networks are cool."

    @patch("src.service.slide_chat_service.genai.Client")
    def test_chat_quiz_returns_response(self, mock_cls, auth_client):
        """POST chat with quiz slide returns AI response."""
        ids = _seed_content(auth_client)
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "ML stands for Machine Learning."
        mock_client.models.generate_content.return_value = mock_response

        resp = auth_client.post(
            "/api/slides/chat",
            json={
                "slide_type": "quiz",
                "quiz_id": ids["quiz_id"],
                "message": "Explain this quiz.",
            },
        )
        assert resp.status_code == 200
        assert "ML" in resp.json()["response"]

    def test_chat_unauthenticated(self, client):
        """POST chat without session returns 401."""
        resp = client.post(
            "/api/slides/chat",
            json={"slide_type": "chapter", "chapter_id": 1, "message": "Hello"},
        )
        assert resp.status_code == 401

    def test_chat_invalid_slide_type(self, auth_client):
        """POST chat with invalid slide_type returns 400."""
        resp = auth_client.post(
            "/api/slides/chat",
            json={"slide_type": "invalid", "message": "Hello"},
        )
        assert resp.status_code == 400

    def test_chat_missing_chapter_id(self, auth_client):
        """POST chat with chapter type but no chapter_id returns 400."""
        resp = auth_client.post(
            "/api/slides/chat",
            json={"slide_type": "chapter", "message": "Hello"},
        )
        assert resp.status_code == 400


class TestSlideChatGet:
    """Tests for GET /api/slides/chat."""

    @patch("src.service.slide_chat_service.genai.Client")
    def test_get_history_returns_messages(self, mock_cls, auth_client):
        """GET chat returns message history ordered by created_at."""
        ids = _seed_content(auth_client)
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Answer."
        mock_client.models.generate_content.return_value = mock_response

        auth_client.post(
            "/api/slides/chat",
            json={
                "slide_type": "chapter",
                "chapter_id": ids["chapter_id"],
                "message": "Q1",
            },
        )
        resp = auth_client.get(
            "/api/slides/chat",
            params={"slide_type": "chapter", "chapter_id": ids["chapter_id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"

    def test_get_history_empty(self, auth_client):
        """GET chat returns empty list for slide with no history."""
        ids = _seed_content(auth_client)
        resp = auth_client.get(
            "/api/slides/chat",
            params={"slide_type": "chapter", "chapter_id": ids["chapter_id"]},
        )
        assert resp.status_code == 200
        assert resp.json() == []
