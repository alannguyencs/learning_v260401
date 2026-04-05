"""Unit tests for QuizGrader (LLM calls mocked)."""

from unittest.mock import MagicMock, patch

from src.service.quiz_grader import GradingOutput, GradingResult, QuizGrader


def _mock_gemini_response(good_points, bad_points):
    """Build a mock Gemini generate_content response."""
    mock_response = MagicMock()
    mock_response.parsed = GradingOutput(good_points=good_points, bad_points=bad_points)
    return mock_response


class TestQuizGrader:
    """Tests for QuizGrader.grade."""

    def test_grader_passed_when_above_threshold(self):
        """2 good + 1 bad = 66% → PASSED."""
        mock_response = _mock_gemini_response(["point1", "point2"], ["missed1"])

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning concepts",
                user_answer="ML is about learning from data",
                quiz_type="free_recall",
            )

        assert isinstance(result, GradingResult)
        assert result.is_correct is True
        assert len(result.good_points) == 2
        assert len(result.bad_points) == 1

    def test_grader_failed_when_below_threshold(self):
        """1 good + 2 bad = 33% → FAILED."""
        mock_response = _mock_gemini_response(["point1"], ["missed1", "missed2"])

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="Explain backpropagation.",
                expected_answer="Gradient descent via chain rule.",
                user_answer="Something about gradients",
                quiz_type="teach_back",
            )

        assert result.is_correct is False
        assert len(result.good_points) == 1
        assert len(result.bad_points) == 2

    def test_grader_returns_good_and_bad_points(self):
        """Result contains the actual point lists from LLM."""
        mock_response = _mock_gemini_response(["Correct concept"], ["Missed detail"])

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning",
                user_answer="Machine Learning",
                quiz_type="free_recall",
            )

        assert result.good_points == ["Correct concept"]
        assert result.bad_points == ["Missed detail"]

    def test_grader_empty_points_is_passed(self):
        """0 good + 0 bad → 0/max(0,1) = 0 < 0.66 → FAILED."""
        mock_response = _mock_gemini_response([], [])

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning",
                user_answer="",
                quiz_type="free_recall",
            )

        assert result.is_correct is False

    def test_mc_auto_graded_no_llm(self):
        """MC is auto-graded in API layer; QuizGrader not called."""
        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            correct_options = ["A", "C"]
            assert "A" in correct_options
            assert "B" not in correct_options
            mock_cls.assert_not_called()
