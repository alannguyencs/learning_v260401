"""Tests for content API endpoints."""

import pytest
from passlib.context import CryptContext

from src.configs import settings
from src.crud.crud_content import list_quizzes_for_chapter
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


class TestCreateBook:
    """Tests for POST /api/content/books."""

    def test_create_book_bearer_auth(self, client):
        """POST /api/content/books with valid Bearer token returns 200."""
        response = client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "Machine Learning"},
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == "ml"
        assert data["title"] == "Machine Learning"

    def test_create_book_unauthorized(self, client):
        """POST /api/content/books without auth returns 401."""
        response = client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "Machine Learning"},
        )
        assert response.status_code == 401

    def test_create_book_wrong_token(self, client):
        """POST /api/content/books with wrong token returns 401."""
        response = client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "Machine Learning"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_create_book_duplicate(self, client):
        """POST /api/content/books with duplicate book_id returns 409."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "Machine Learning"},
            headers=BEARER_HEADER,
        )
        response = client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "Duplicate"},
            headers=BEARER_HEADER,
        )
        assert response.status_code == 409


class TestCreateLesson:
    """Tests for POST /api/content/lessons."""

    def test_create_lesson_in_book(self, client):
        """POST /api/content/lessons returns 200 with lesson_index stored."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "ML"},
            headers=BEARER_HEADER,
        )
        response = client.post(
            "/api/content/lessons",
            json={"book_id": "ml", "lesson_index": 1, "title": "Intro"},
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == "ml"
        assert data["lesson_index"] == 1

    def test_create_lesson_book_not_found(self, client):
        """POST /api/content/lessons with unknown book_id returns 404."""
        response = client.post(
            "/api/content/lessons",
            json={"book_id": "nonexistent", "lesson_index": 1, "title": "Intro"},
            headers=BEARER_HEADER,
        )
        assert response.status_code == 404


class TestCreateChapter:
    """Tests for POST /api/content/chapters."""

    def test_create_chapter(self, client):
        """POST /api/content/chapters returns 200."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "ML"},
            headers=BEARER_HEADER,
        )
        lesson_resp = client.post(
            "/api/content/lessons",
            json={"book_id": "ml", "lesson_index": 1, "title": "Intro"},
            headers=BEARER_HEADER,
        )
        lesson_id = lesson_resp.json()["id"]
        response = client.post(
            "/api/content/chapters",
            json={
                "lesson_id": lesson_id,
                "chapter_index": 1,
                "title": "Ch1",
                "content": "# Chapter 1",
            },
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_index"] == 1


class TestUploadQuizzes:
    """Tests for POST /api/content/quizzes."""

    def _setup_chapter(self, client):
        """Helper to create book/lesson/chapter and return chapter_id."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "ML"},
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
        return chapter_resp.json()["id"]

    def test_upload_quizzes_mc(self, client):
        """POST /api/content/quizzes with MC type stores correct_options."""
        chapter_id = self._setup_chapter(client)
        response = client.post(
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
        assert response.status_code == 200
        assert response.json()["inserted"] == 1

    def test_upload_quizzes_open_ended(self, client):
        """POST /api/content/quizzes with free_recall type stores expected_answer."""
        chapter_id = self._setup_chapter(client)
        response = client.post(
            "/api/content/quizzes",
            json={
                "chapter_id": chapter_id,
                "quizzes": [
                    {
                        "quiz_type": "free_recall",
                        "question": "Explain ML.",
                        "expected_answer": "ML is machine learning.",
                    }
                ],
            },
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200
        assert response.json()["inserted"] == 1

    def test_upload_quiz_with_rich_metadata(self, client, db_session):
        """POST /api/content/quizzes with rich metadata fields stores all new columns."""
        chapter_id = self._setup_chapter(client)
        response = client.post(
            "/api/content/quizzes",
            json={
                "chapter_id": chapter_id,
                "quizzes": [
                    {
                        "quiz_type": "free_recall",
                        "question": "Describe the FBI framework.",
                        "expected_answer": "Emergency, Essentials, Equity, Enjoyment.",
                        "section_index": 1,
                        "section_name": "Summary",
                        "quiz_take_away": "FBI forces discipline by funding Enjoyment last.",
                        "quiz_metadata": {"key_points": ["Emergency first", "Enjoyment last"]},
                    }
                ],
            },
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200
        assert response.json()["inserted"] == 1

        quizzes = list_quizzes_for_chapter(db_session, chapter_id)
        assert len(quizzes) == 1
        q = quizzes[0]
        assert q.section_index == 1
        assert q.section_name == "Summary"
        assert q.quiz_take_away == "FBI forces discipline by funding Enjoyment last."
        assert q.quiz_metadata == {"key_points": ["Emergency first", "Enjoyment last"]}

    def test_upload_cloze_quiz_metadata(self, client, db_session):
        """POST cloze quiz with blanks in quiz_metadata stores JSONB correctly."""
        chapter_id = self._setup_chapter(client)
        response = client.post(
            "/api/content/quizzes",
            json={
                "chapter_id": chapter_id,
                "quizzes": [
                    {
                        "quiz_type": "cloze",
                        "question": "The happiness equation is ___.",
                        "expected_answer": "H = O/D",
                        "section_index": 1,
                        "section_name": "Summary",
                        "quiz_metadata": {"blanks": ["H = O/D"], "context_hint": ""},
                    }
                ],
            },
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200

        quizzes = list_quizzes_for_chapter(db_session, chapter_id)
        assert quizzes[0].quiz_metadata["blanks"] == ["H = O/D"]

    def test_upload_mc_quiz_with_option_explanations(self, client, db_session):
        """POST MC quiz with response_to_user_option_* in quiz_metadata stores correctly."""
        chapter_id = self._setup_chapter(client)
        metadata = {
            "quiz_type_cognitive": "recall",
            "quiz_learnt": "Two index fund rules",
            "response_to_user_option_a": "Incorrect — timing the market fails.",
            "response_to_user_option_b": "Correct — put in and never sell.",
            "response_to_user_option_c": "Incorrect — not in lesson.",
            "response_to_user_option_d": "Incorrect — not mentioned.",
        }
        response = client.post(
            "/api/content/quizzes",
            json={
                "chapter_id": chapter_id,
                "quizzes": [
                    {
                        "quiz_type": "multiple_choice",
                        "question": "What are the two index fund rules?",
                        "option_a": "Buy low sell high",
                        "option_b": "Put in and never sell",
                        "option_c": "Diversify",
                        "option_d": "Rebalance quarterly",
                        "correct_options": ["B"],
                        "quiz_metadata": metadata,
                    }
                ],
            },
            headers=BEARER_HEADER,
        )
        assert response.status_code == 200

        quizzes = list_quizzes_for_chapter(db_session, chapter_id)
        stored = quizzes[0].quiz_metadata
        assert stored["quiz_type_cognitive"] == "recall"
        assert stored["response_to_user_option_b"] == "Correct — put in and never sell."


class TestListBooks:
    """Tests for GET /api/content/books."""

    def test_list_books(self, client, auth_client):  # pylint: disable=redefined-outer-name
        """GET /api/content/books (session auth) returns list."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "ML"},
            headers=BEARER_HEADER,
        )
        response = auth_client.get("/api/content/books")
        assert response.status_code == 200
        books = response.json()
        assert any(b["book_id"] == "ml" for b in books)

    def test_list_books_unauthenticated(self, client):
        """GET /api/content/books without session returns 401."""
        response = client.get("/api/content/books")
        assert response.status_code == 401


class TestBookStructure:
    """Tests for GET /api/content/books/{book_id}/structure."""

    def test_book_structure(self, client, auth_client):  # pylint: disable=redefined-outer-name
        """GET /api/content/books/{id}/structure returns full tree."""
        client.post(
            "/api/content/books",
            json={"book_id": "ml", "title": "ML"},
            headers=BEARER_HEADER,
        )
        lesson_resp = client.post(
            "/api/content/lessons",
            json={"book_id": "ml", "lesson_index": 1, "title": "Intro"},
            headers=BEARER_HEADER,
        )
        lesson_id = lesson_resp.json()["id"]
        client.post(
            "/api/content/chapters",
            json={
                "lesson_id": lesson_id,
                "chapter_index": 1,
                "title": "Ch1",
                "content": "# Chapter 1",
            },
            headers=BEARER_HEADER,
        )
        response = auth_client.get("/api/content/books/ml/structure")
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == "ml"
        assert len(data["lessons"]) == 1
        assert data["lessons"][0]["lesson_index"] == 1
        assert len(data["lessons"][0]["chapters"]) == 1
        assert data["lessons"][0]["chapters"][0]["quiz_count"] == 0

    def test_book_structure_not_found(self, auth_client):  # pylint: disable=redefined-outer-name
        """GET /api/content/books/{id}/structure for unknown book returns 404."""
        response = auth_client.get("/api/content/books/nonexistent/structure")
        assert response.status_code == 404
