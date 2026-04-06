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
    client.post(
        "/api/login/",
        json={"username": "testuser", "password": "testpass"},
    )
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
        resp = client.get("/api/dashboard/learning-progress")
        assert resp.status_code == 401


class TestLearningProgressEmpty:
    """Empty/zero-progress state tests."""

    def test_learning_progress_empty(self, auth_client):  # pylint: disable=redefined-outer-name
        """Returns books with empty lesson data when no activity."""
        _seed_content(auth_client)
        resp = auth_client.get("/api/dashboard/learning-progress")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        book = data[0]
        assert book["book_id"] == "ml"
        assert book["book_title"] == "Machine Learning"
        assert len(book["lessons"]) == 1
        assert book["lessons"][0]["lesson_title"] == "Intro"
        assert book["lessons"][0]["total_answers"] == 0
        assert book["lessons"][0]["round_num"] is None
        assert book["accuracy_trend"] == []


class TestLearningProgressWithLessonData:
    """Lesson table data tests."""

    def test_lesson_has_round_and_accuracy(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Lesson row has round_num and accuracy after interaction."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        slide = auth_client.get("/api/slides/next").json().get("quiz")
        if slide is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{slide['id']}/respond",
            json={
                "round_num": slide["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",
                "is_skip": False,
            },
        )

        resp = auth_client.get("/api/dashboard/learning-progress")
        lesson = resp.json()[0]["lessons"][0]
        assert lesson["round_num"] == 0
        assert lesson["round_status"] == "open"
        assert lesson["total_answers"] == 1
        assert lesson["correct_answers"] == 1


class TestLearningProgressAccuracyTrend:
    """Accuracy trendline tests."""

    def test_accuracy_trend_empty_under_20(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """accuracy_trend is [] when fewer than 20 answers."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        slide = auth_client.get("/api/slides/next").json().get("quiz")
        if slide is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{slide['id']}/respond",
            json={
                "round_num": slide["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",
                "is_skip": False,
            },
        )

        resp = auth_client.get("/api/dashboard/learning-progress")
        assert resp.json()[0]["accuracy_trend"] == []


class TestLearningProgressGroupedByBook:
    """Grouping tests."""

    def test_one_entry_per_book(self, auth_client):  # pylint: disable=redefined-outer-name
        """Each book produces one entry."""
        _seed_content(auth_client)
        auth_client.post(
            "/api/content/books",
            json={"book_id": "dl", "title": "Deep Learning"},
            headers=BEARER_HEADER,
        )
        auth_client.post(
            "/api/content/lessons",
            json={
                "book_id": "dl",
                "lesson_index": 1,
                "title": "DL Intro",
            },
            headers=BEARER_HEADER,
        )

        resp = auth_client.get("/api/dashboard/learning-progress")
        data = resp.json()
        book_ids = [b["book_id"] for b in data]
        assert len(book_ids) == 2
        assert sorted(book_ids) == book_ids


class TestAccuracyTrendAlgorithm:
    """Unit tests for _compute_accuracy_trend."""

    @staticmethod
    def _trend(answers):
        from src.crud.crud_dashboard import (  # pylint: disable=import-outside-toplevel
            _compute_accuracy_trend,
        )

        return _compute_accuracy_trend(answers)

    def test_under_20_returns_empty(self):
        """Fewer than 20 answers returns empty trend."""
        assert not self._trend([True] * 19)

    def test_exactly_20_returns_20_points(self):
        """20 answers returns 20 points with window_size=1."""
        answers = [False] * 10 + [True] * 10
        trend = self._trend(answers)
        assert len(trend) == 20
        assert trend[0] == 0
        assert trend[-1] == 100

    def test_50_answers_returns_20_points(self):
        """50 answers returns 20 points with window_size=31."""
        answers = [True] * 50
        trend = self._trend(answers)
        assert len(trend) == 20
        assert all(p == 100 for p in trend)

    def test_119_answers_returns_20_points(self):
        """119 answers returns 20 points with window_size=100."""
        trend = self._trend([True] * 119)
        assert len(trend) == 20
        assert all(p == 100 for p in trend)

    def test_sliding_window_correctness(self):
        """Verify sliding window values shift correctly."""
        answers = [False] * 19 + [True] * 100
        trend = self._trend(answers)
        assert len(trend) == 20
        assert trend[0] == 81
        assert trend[-1] == 100
