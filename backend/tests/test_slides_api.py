"""Tests for slide API endpoints."""

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
def auth_client(client, db_session):  # pylint: disable=redefined-outer-name
    """Client with a logged-in session user."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "testuser", hashed)
    client.post("/api/login/", json={"username": "testuser", "password": "testpass"})
    return client


def _seed_content(client):
    """Create book/lesson/chapter with quizzes; return ids."""
    client.post(
        "/api/content/books",
        json={"book_id": "ml", "title": "Machine Learning"},
        headers=BEARER_HEADER,
    )
    lesson_resp = client.post(
        "/api/content/lessons",
        json={"book_id": "ml", "lesson_index": 1, "title": "Intro"},
        headers=BEARER_HEADER,
    )
    lesson_id = lesson_resp.json()["id"]
    chapter_resp = client.post(
        "/api/content/chapters",
        json={
            "lesson_id": lesson_id,
            "chapter_index": 1,
            "title": "Ch1",
            "content": "# Chapter 1",
        },
        headers=BEARER_HEADER,
    )
    chapter_id = chapter_resp.json()["id"]
    quiz_resp = client.post(
        "/api/content/quizzes",
        json={
            "chapter_id": chapter_id,
            "quizzes": [
                {
                    "quiz_type": "multiple_choice",
                    "question": "What is ML?",
                    "option_a": "A",
                    "option_b": "B",
                    "option_c": "C",
                    "option_d": "D",
                    "correct_options": ["A"],
                }
            ],
        },
        headers=BEARER_HEADER,
    )
    return {
        "lesson_id": lesson_id,
        "chapter_id": chapter_id,
        "quiz_count": quiz_resp.json()["inserted"],
    }


class TestMarkChapterLearnt:
    """Tests for POST /api/slides/chapters/{id}/learnt."""

    def test_mark_chapter_learnt(self, auth_client):  # pylint: disable=redefined-outer-name
        """POST mark-learnt returns lesson_fully_learnt and lesson_count."""
        ids = _seed_content(auth_client)
        response = auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        assert response.status_code == 200
        data = response.json()
        assert "lesson_fully_learnt" in data
        assert "lesson_count" in data
        assert data["lesson_fully_learnt"] is True
        assert data["lesson_count"] == 1

    def test_mark_chapter_learnt_unauthenticated(self, client):
        """POST mark-learnt without session returns 401."""
        response = client.post("/api/slides/chapters/1/learnt")
        assert response.status_code == 401


class TestRespondToQuiz:
    """Tests for POST /api/slides/quizzes/{id}/respond."""

    def _get_quiz_id(self, auth_client):  # pylint: disable=redefined-outer-name
        """Seed content, mark chapter learnt, return quiz_id and lesson_id."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        # Get the current slide to find the quiz
        slide_resp = auth_client.get("/api/slides/current")
        quiz = slide_resp.json().get("quiz")
        if quiz:
            return quiz["id"], ids["lesson_id"]
        return None, ids["lesson_id"]

    def test_respond_mc_correct(self, auth_client):  # pylint: disable=redefined-outer-name
        """MC with correct answer → is_correct=true."""
        quiz_id, lesson_id = self._get_quiz_id(auth_client)
        if quiz_id is None:
            pytest.skip("No quiz slide available")
        response = auth_client.post(
            f"/api/slides/quizzes/{quiz_id}/respond",
            json={"round_num": 0, "lesson_id": lesson_id, "user_answer": "A", "is_skip": False},
        )
        assert response.status_code == 200
        assert response.json()["is_correct"] is True

    def test_respond_mc_incorrect(self, auth_client):  # pylint: disable=redefined-outer-name
        """MC with wrong answer → is_correct=false."""
        quiz_id, lesson_id = self._get_quiz_id(auth_client)
        if quiz_id is None:
            pytest.skip("No quiz slide available")
        response = auth_client.post(
            f"/api/slides/quizzes/{quiz_id}/respond",
            json={"round_num": 0, "lesson_id": lesson_id, "user_answer": "D", "is_skip": False},
        )
        assert response.status_code == 200
        assert response.json()["is_correct"] is False

    def test_respond_skip(self, auth_client):  # pylint: disable=redefined-outer-name
        """is_skip=true → is_correct=null, no recall update."""
        quiz_id, lesson_id = self._get_quiz_id(auth_client)
        if quiz_id is None:
            pytest.skip("No quiz slide available")
        response = auth_client.post(
            f"/api/slides/quizzes/{quiz_id}/respond",
            json={"round_num": 0, "lesson_id": lesson_id, "user_answer": "", "is_skip": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is None

    def test_respond_quiz_not_found(self, auth_client):  # pylint: disable=redefined-outer-name
        """POST respond to non-existent quiz returns 404."""
        response = auth_client.post(
            "/api/slides/quizzes/9999/respond",
            json={"round_num": 0, "lesson_id": 1, "user_answer": "A", "is_skip": False},
        )
        assert response.status_code == 404


class TestGetCurrentSlide:
    """Tests for GET /api/slides/current."""

    def test_get_current_slide_chapter(self, auth_client):  # pylint: disable=redefined-outer-name
        """Fresh user with content gets a chapter slide."""
        _seed_content(auth_client)
        response = auth_client.get("/api/slides/current")
        assert response.status_code == 200
        data = response.json()
        assert data["slide_type"] == "chapter"
        assert data["chapter"] is not None
        assert "has_previous" in data

    def test_get_current_slide_quiz_after_chapter(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """After marking chapter learnt, current slide is a quiz (R0 due immediately)."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        response = auth_client.get("/api/slides/current")
        assert response.status_code == 200
        data = response.json()
        assert data["slide_type"] == "quiz"

    def test_get_current_slide_unauthenticated(self, client):
        """GET /api/slides/current without session returns 401."""
        response = client.get("/api/slides/current")
        assert response.status_code == 401

    def test_get_current_slide_none_when_empty(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """No content → slide_type=none."""
        response = auth_client.get("/api/slides/current")
        assert response.status_code == 200
        assert response.json()["slide_type"] == "none"
