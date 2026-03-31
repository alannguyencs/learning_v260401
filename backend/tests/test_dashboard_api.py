"""Tests for GET /api/dashboard/activity-log."""

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
    """Create book/lesson/chapter/quiz and return ids dict."""
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


class TestActivityLogUnauthenticated:
    """Auth guard tests."""

    def test_activity_log_unauthenticated(self, client):
        """GET activity-log without session returns 401."""
        response = client.get("/api/dashboard/activity-log")
        assert response.status_code == 401


class TestActivityLogEmpty:
    """Empty state tests."""

    def test_activity_log_empty(self, auth_client):  # pylint: disable=redefined-outer-name
        """Authenticated user with no activity returns empty list."""
        response = auth_client.get("/api/dashboard/activity-log")
        assert response.status_code == 200
        assert response.json() == []


class TestActivityLogLearntChapter:
    """LEARNT CHAPTER event tests."""

    def test_learnt_chapter_appears(self, auth_client):  # pylint: disable=redefined-outer-name
        """After marking chapter learnt, a LEARNT CHAPTER row appears."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        response = auth_client.get("/api/dashboard/activity-log")
        assert response.status_code == 200
        entries = response.json()
        actions = [e["action"] for e in entries]
        assert "LEARNT CHAPTER" in actions

        learnt = next(e for e in entries if e["action"] == "LEARNT CHAPTER")
        assert learnt["chapter_id"] == ids["chapter_id"]
        assert learnt["book_id"] == "ml"
        assert learnt["lesson_index"] == 1
        assert learnt["answer_result"] is None
        assert learnt["recall_rate"] is None


class TestActivityLogSkip:
    """SKIP event tests."""

    def test_skip_appears(self, auth_client):  # pylint: disable=redefined-outer-name
        """After skipping a quiz, a SKIP row appears with null answer_result and recall_rate."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        slide_resp = auth_client.get("/api/slides/next")
        quiz = slide_resp.json().get("quiz")
        if quiz is None:
            pytest.skip("No quiz available after marking chapter learnt")

        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": quiz["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "",
                "is_skip": True,
            },
        )

        response = auth_client.get("/api/dashboard/activity-log")
        entries = response.json()
        skip_rows = [e for e in entries if e["action"] == "SKIP"]
        assert len(skip_rows) >= 1
        assert skip_rows[0]["answer_result"] is None
        assert skip_rows[0]["recall_rate"] is None


class TestActivityLogAnswer:
    """ANSWER event tests."""

    def _get_quiz(self, auth_client, ids):
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        slide_resp = auth_client.get("/api/slides/next")
        return slide_resp.json().get("quiz")

    def test_wrong_answer_appears(self, auth_client):  # pylint: disable=redefined-outer-name
        """Wrong answer produces ANSWER row with answer_result='wrong' and recall_rate=1.2."""
        ids = _seed_content(auth_client)
        quiz = self._get_quiz(auth_client, ids)
        if quiz is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": quiz["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "D",  # wrong
                "is_skip": False,
            },
        )

        response = auth_client.get("/api/dashboard/activity-log")
        entries = response.json()
        answer_rows = [e for e in entries if e["action"] == "ANSWER"]
        assert len(answer_rows) == 1
        assert answer_rows[0]["answer_result"] == "wrong"
        assert answer_rows[0]["recall_rate"] == 1.2

    def test_correct_answer_appears(self, auth_client):  # pylint: disable=redefined-outer-name
        """Correct answer produces ANSWER row with answer_result='correct' and recall_rate<1."""
        ids = _seed_content(auth_client)
        quiz = self._get_quiz(auth_client, ids)
        if quiz is None:
            pytest.skip("No quiz available")

        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": quiz["round_num"],
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",  # correct
                "is_skip": False,
            },
        )

        response = auth_client.get("/api/dashboard/activity-log")
        entries = response.json()
        answer_rows = [e for e in entries if e["action"] == "ANSWER"]
        assert len(answer_rows) == 1
        assert answer_rows[0]["answer_result"] == "correct"
        assert answer_rows[0]["recall_rate"] < 1.0


class TestActivityLogOrdering:
    """Chronological ordering tests."""

    def test_rows_ordered_by_time(self, auth_client):  # pylint: disable=redefined-outer-name
        """All rows are sorted by event_time ascending."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        slide_resp = auth_client.get("/api/slides/next")
        quiz = slide_resp.json().get("quiz")
        if quiz:
            auth_client.post(
                f"/api/slides/quizzes/{quiz['id']}/respond",
                json={
                    "round_num": quiz["round_num"],
                    "lesson_id": ids["lesson_id"],
                    "user_answer": "A",
                    "is_skip": False,
                },
            )

        response = auth_client.get("/api/dashboard/activity-log")
        entries = response.json()
        times = [e["event_time"] for e in entries if e["event_time"]]
        assert times == sorted(times)


class TestActivityLogRoundCreated:
    """ROUND CREATED event tests."""

    def test_round_created_appears(self, auth_client):  # pylint: disable=redefined-outer-name
        """After marking chapter learnt, a ROUND CREATED row appears."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")

        response = auth_client.get("/api/dashboard/activity-log")
        entries = response.json()
        round_rows = [e for e in entries if e["action"].startswith("ROUND CREATED")]
        assert len(round_rows) >= 1
        assert round_rows[0]["chapter_id"] is None
        assert round_rows[0]["answer_result"] is None
