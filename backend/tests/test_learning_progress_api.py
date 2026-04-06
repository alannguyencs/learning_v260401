"""Tests for GET /api/dashboard/learning-progress."""

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
    """Create book/lesson/2 chapters/quiz and return ids dict."""
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
    ch1_resp = client.post(
        "/api/content/chapters",
        json={
            "lesson_id": lesson_id,
            "chapter_index": 1,
            "title": "Ch1",
            "content": "# Chapter 1",
        },
        headers=BEARER_HEADER,
    )
    chapter_id = ch1_resp.json()["id"]
    client.post(
        "/api/content/chapters",
        json={
            "lesson_id": lesson_id,
            "chapter_index": 2,
            "title": "Ch2",
            "content": "# Chapter 2",
        },
        headers=BEARER_HEADER,
    )
    client.post(
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
    return {"lesson_id": lesson_id, "chapter_id": chapter_id}


class TestLearningProgressUnauthenticated:
    """Auth guard tests."""

    def test_learning_progress_unauthenticated(self, client):
        """GET learning-progress without session returns 401."""
        response = client.get("/api/dashboard/learning-progress")
        assert response.status_code == 401


class TestLearningProgressEmpty:
    """Empty/zero-progress state tests."""

    def test_learning_progress_empty(self, auth_client):
        """Returns lessons with zero progress when user has no activity."""
        _seed_content(auth_client)
        response = auth_client.get("/api/dashboard/learning-progress")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        lesson = data[0]
        assert lesson["book_id"] == "ml"
        assert lesson["lesson_title"] == "Intro"
        assert lesson["total_chapters"] == 2
        assert lesson["learnt_chapters"] == 0
        assert lesson["round_num"] is None
        assert lesson["total_answers"] == 0
        assert lesson["avg_forgetting_rate"] is None


class TestLearningProgressWithChapter:
    """Chapter learnt metric tests."""

    def test_learning_progress_with_chapter_learnt(self, auth_client):
        """learnt_chapters increments after marking a chapter."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        response = auth_client.get("/api/dashboard/learning-progress")
        data = response.json()
        assert data[0]["learnt_chapters"] == 1
        assert data[0]["total_chapters"] == 2


class TestLearningProgressWithQuiz:
    """Quiz accuracy metric tests."""

    def test_learning_progress_with_quiz_answers(self, auth_client):
        """total_answers and correct_answers reflect quiz_answer_log data."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        slide_resp = auth_client.get("/api/slides/next")
        quiz = slide_resp.json().get("quiz")
        if quiz is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": quiz["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",
                "is_skip": False,
            },
        )

        response = auth_client.get("/api/dashboard/learning-progress")
        data = response.json()
        assert data[0]["total_answers"] == 1
        assert data[0]["correct_answers"] == 1


class TestLearningProgressWithRevision:
    """Revision round metric tests."""

    def test_learning_progress_with_revision_round(self, auth_client):
        """round_num and round_status populated after chapter learnt."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        response = auth_client.get("/api/dashboard/learning-progress")
        data = response.json()
        assert data[0]["round_num"] == 0
        assert data[0]["round_status"] == "open"
        assert data[0]["quizzes_in_round"] is not None


class TestLearningProgressWithRecall:
    """Recall metric tests."""

    def test_learning_progress_with_recall(self, auth_client):
        """avg_forgetting_rate computed after quiz response."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        slide_resp = auth_client.get("/api/slides/next")
        quiz = slide_resp.json().get("quiz")
        if quiz is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": quiz["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",
                "is_skip": False,
            },
        )

        response = auth_client.get("/api/dashboard/learning-progress")
        data = response.json()
        assert data[0]["avg_forgetting_rate"] is not None
        assert isinstance(data[0]["avg_forgetting_rate"], float)


class TestLearningProgressOrdering:
    """Ordering tests."""

    def test_learning_progress_grouped_by_book(self, auth_client):
        """Lessons ordered by book_id then lesson_index."""
        _seed_content(auth_client)
        # Add a second book
        auth_client.post(
            "/api/content/books",
            json={"book_id": "dl", "title": "Deep Learning"},
            headers=BEARER_HEADER,
        )
        auth_client.post(
            "/api/content/lessons",
            json={"book_id": "dl", "lesson_index": 1, "title": "DL Intro"},
            headers=BEARER_HEADER,
        )

        response = auth_client.get("/api/dashboard/learning-progress")
        data = response.json()
        book_ids = [d["book_id"] for d in data]
        assert book_ids == sorted(book_ids)
