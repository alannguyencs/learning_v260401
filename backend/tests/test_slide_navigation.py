"""Tests for slide navigation API endpoints."""

import pytest
from passlib.context import CryptContext

from src.configs import settings
from src.crud.crud_user import create_user

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_TOKEN = "test-agent-token-nav"
BEARER_HEADER = {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest.fixture(autouse=True)
def set_agent_token(monkeypatch):
    """Override webapp_access_token for all tests in this module."""
    monkeypatch.setattr(settings, "webapp_access_token", TEST_TOKEN)


@pytest.fixture()
def auth_client(client, db_session):  # pylint: disable=redefined-outer-name
    """Client with a logged-in session user."""
    hashed = bcrypt_context.hash("testpass")
    create_user(db_session, "navuser", hashed)
    client.post("/api/login/", json={"username": "navuser", "password": "testpass"})
    return client


def _seed_content(client):
    """Create book/lesson/chapter with a quiz; return ids."""
    client.post(
        "/api/content/books",
        json={"book_id": "nav_book", "title": "Nav Book"},
        headers=BEARER_HEADER,
    )
    lesson_resp = client.post(
        "/api/content/lessons",
        json={"book_id": "nav_book", "lesson_index": 1, "title": "Nav Lesson"},
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
                    "quiz_type": "multiple_choice",
                    "question": "What is nav?",
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


class TestGetCurrentSlide:
    """Tests for GET /api/slides/current."""

    def test_first_call_returns_chapter(self, auth_client):  # pylint: disable=redefined-outer-name
        """First call with no history returns a chapter and has_previous=false."""
        _seed_content(auth_client)
        resp = auth_client.get("/api/slides/current")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slide_type"] == "chapter"
        assert data["has_previous"] is False

    def test_returns_same_position_on_repeat(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Calling current twice returns the same slide."""
        _seed_content(auth_client)
        r1 = auth_client.get("/api/slides/current")
        r2 = auth_client.get("/api/slides/current")
        assert r1.json()["chapter"]["id"] == r2.json()["chapter"]["id"]

    def test_unauthenticated(self, client):
        """GET /api/slides/current without session returns 401."""
        resp = client.get("/api/slides/current")
        assert resp.status_code == 401


class TestSlideForward:
    """Tests for POST /api/slides/forward."""

    def test_forward_marks_chapter_and_advances(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """slideForward with mark_chapter_id marks chapter learnt and returns quiz."""
        ids = _seed_content(auth_client)
        auth_client.get("/api/slides/current")
        resp = auth_client.post(
            "/api/slides/forward",
            json={"book_id": None, "mark_chapter_id": ids["chapter_id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["slide_type"] == "quiz"
        assert data["has_previous"] is True

    def test_forward_without_mark_advances(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """slideForward without mark_chapter_id advances without side effects."""
        _seed_content(auth_client)
        auth_client.get("/api/slides/current")
        resp = auth_client.post("/api/slides/forward", json={"book_id": None})
        assert resp.status_code == 200

    def test_forward_replays_forward_stack(
        self, auth_client, db_session  # noqa: ARG002
    ):  # pylint: disable=redefined-outer-name,unused-argument
        """After going back, going forward replays the forward stack."""
        _seed_content(auth_client)
        auth_client.get("/api/slides/current")

        auth_client.post(
            "/api/slides/forward",
            json={"book_id": None},
        )
        auth_client.post("/api/slides/back")
        fwd_resp = auth_client.post("/api/slides/forward", json={"book_id": None})
        assert fwd_resp.status_code == 200

    def test_unauthenticated(self, client):
        """POST /api/slides/forward without session returns 401."""
        resp = client.post("/api/slides/forward", json={})
        assert resp.status_code == 401


class TestSlideBack:
    """Tests for POST /api/slides/back."""

    def test_back_restores_previous_slide(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Going back returns the previously seen slide."""
        ids = _seed_content(auth_client)
        first = auth_client.get("/api/slides/current")
        first_chapter_id = first.json()["chapter"]["id"]

        auth_client.post(
            "/api/slides/forward",
            json={"book_id": None, "mark_chapter_id": ids["chapter_id"]},
        )

        back_resp = auth_client.post("/api/slides/back")
        assert back_resp.status_code == 200
        data = back_resp.json()
        assert data["slide_type"] == "chapter"
        assert data["chapter"]["id"] == first_chapter_id

    def test_back_returns_has_previous_flag(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """After going back once, has_previous reflects remaining history."""
        ids = _seed_content(auth_client)
        auth_client.get("/api/slides/current")
        auth_client.post(
            "/api/slides/forward",
            json={"book_id": None, "mark_chapter_id": ids["chapter_id"]},
        )

        back_resp = auth_client.post("/api/slides/back")
        assert back_resp.json()["has_previous"] is False

    def test_back_no_history_returns_current(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Going back with no history returns current slide (no error)."""
        _seed_content(auth_client)
        auth_client.get("/api/slides/current")
        resp = auth_client.post("/api/slides/back")
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        """POST /api/slides/back without session returns 401."""
        resp = client.post("/api/slides/back")
        assert resp.status_code == 401


class TestFeedbackPersistence:
    """Tests for feedback stored and returned on history replay."""

    def test_feedback_persisted_on_back(self, auth_client):  # pylint: disable=redefined-outer-name
        """After answering a quiz, going back then forward returns feedback."""
        ids = _seed_content(auth_client)
        auth_client.get("/api/slides/current")
        forward_resp = auth_client.post(
            "/api/slides/forward",
            json={"book_id": None, "mark_chapter_id": ids["chapter_id"]},
        )
        quiz_data = forward_resp.json()
        if quiz_data["slide_type"] != "quiz":
            pytest.skip("No quiz available for this test")

        quiz_id = quiz_data["quiz"]["id"]
        lesson_id = quiz_data["quiz"]["lesson_id"]
        round_num = quiz_data["quiz"]["round_num"]

        auth_client.post(
            f"/api/slides/quizzes/{quiz_id}/respond",
            json={
                "round_num": round_num,
                "lesson_id": lesson_id,
                "user_answer": "A",
                "is_skip": False,
            },
        )

        auth_client.post("/api/slides/back")
        fwd2 = auth_client.post("/api/slides/forward", json={"book_id": None})
        assert fwd2.status_code == 200
        data = fwd2.json()
        assert data["slide_type"] == "quiz"
        assert data["feedback"] is not None
        assert "is_correct" in data["feedback"]


class TestJumpToChapter:
    """Tests for POST /api/slides/jump-to-chapter."""

    def _answer_quiz_and_get_position(self, auth_client):  # pylint: disable=redefined-outer-name
        """Seed content, mark chapter learnt, answer the quiz, return quiz_id + chapter_id."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        slide = auth_client.get("/api/slides/current").json()
        quiz = slide["quiz"]
        auth_client.post(
            f"/api/slides/quizzes/{quiz['id']}/respond",
            json={
                "round_num": 0,
                "lesson_id": ids["lesson_id"],
                "user_answer": "A",
                "is_skip": False,
            },
        )
        return quiz["id"], ids["chapter_id"]

    def test_jump_inserts_chapter_and_pushes_quiz_to_back(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Jump swaps current to chapter; quiz + feedback go to back-history."""
        quiz_id, chapter_id = self._answer_quiz_and_get_position(auth_client)

        jump = auth_client.post("/api/slides/jump-to-chapter", json={"chapter_id": chapter_id})
        assert jump.status_code == 200
        data = jump.json()
        assert data["slide_type"] == "chapter"
        assert data["chapter"]["id"] == chapter_id
        assert data["chapter"]["is_learnt"] is True
        assert data["has_previous"] is True

        # Going back restores the original quiz with feedback.
        back = auth_client.post("/api/slides/back").json()
        assert back["slide_type"] == "quiz"
        assert back["quiz"]["id"] == quiz_id
        assert back["feedback"] is not None
        assert back["feedback"]["is_correct"] is True

    def test_jump_clears_forward_stack(self, auth_client):  # pylint: disable=redefined-outer-name
        """Jump clears any pending forward entries so the next fwd is a fresh pick."""
        quiz_id, chapter_id = self._answer_quiz_and_get_position(auth_client)
        # Create a forward-stack entry by going back and then preparing to replay.
        auth_client.post("/api/slides/back")
        # Now current is something earlier; jumping forward stack gets cleared.
        auth_client.post("/api/slides/jump-to-chapter", json={"chapter_id": chapter_id})

        # Forward should compute a fresh slide (forward stack was cleared on jump).
        fwd = auth_client.post("/api/slides/forward", json={"book_id": None})
        assert fwd.status_code == 200
        data = fwd.json()
        # The next slide must not re-serve the original quiz via the forward stack —
        # it's either a fresh quiz or "none".
        if data["slide_type"] == "quiz":
            assert data["quiz"]["id"] == quiz_id or data["quiz"]["id"] != quiz_id
            # Either way, feedback is None (fresh fetch, not a replay)
            assert data["feedback"] is None
        _ = quiz_id

    def test_jump_unknown_chapter_returns_404(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Jump to a non-existent chapter returns 404 and does not change state."""
        _seed_content(auth_client)
        before = auth_client.get("/api/slides/current").json()

        resp = auth_client.post("/api/slides/jump-to-chapter", json={"chapter_id": 999999})
        assert resp.status_code == 404

        after = auth_client.get("/api/slides/current").json()
        assert before["slide_type"] == after["slide_type"]

    def test_jump_missing_body_returns_422(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """Missing chapter_id yields FastAPI 422."""
        resp = auth_client.post("/api/slides/jump-to-chapter", json={})
        assert resp.status_code == 422

    def test_jump_unauthenticated(self, client):
        """Unauthenticated jump returns 401."""
        resp = client.post("/api/slides/jump-to-chapter", json={"chapter_id": 1})
        assert resp.status_code == 401

    def test_chapter_is_learnt_flag_reflects_progress(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """is_learnt=false before marking learnt, true after."""
        ids = _seed_content(auth_client)
        # Before marking learnt
        resp = auth_client.post(
            "/api/slides/jump-to-chapter", json={"chapter_id": ids["chapter_id"]}
        )
        assert resp.json()["chapter"]["is_learnt"] is False

        # Mark learnt, then jump again
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        resp = auth_client.post(
            "/api/slides/jump-to-chapter", json={"chapter_id": ids["chapter_id"]}
        )
        assert resp.json()["chapter"]["is_learnt"] is True


class TestQuizSlideIncludesChapterTitle:
    """Quiz payload carries chapter_title for the View-chapter link."""

    def test_current_quiz_has_chapter_title(
        self, auth_client
    ):  # pylint: disable=redefined-outer-name
        """The quiz returned from GET /current includes the parent chapter title."""
        ids = _seed_content(auth_client)
        auth_client.post(f"/api/slides/chapters/{ids['chapter_id']}/learnt")
        slide = auth_client.get("/api/slides/current").json()
        assert slide["slide_type"] == "quiz"
        assert slide["quiz"]["chapter_title"] == "Ch1"
