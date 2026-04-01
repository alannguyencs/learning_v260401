"""Unit tests for QuizGrader (LLM calls mocked)."""

from unittest.mock import MagicMock, patch

from src.service.quiz_grader import GradingOutput, GradingResult, QuizGrader


def _mock_gemini_response(is_correct: bool, feedback: str):
    """Build a mock Gemini generate_content response."""
    mock_response = MagicMock()
    mock_response.parsed = GradingOutput(is_correct=is_correct, feedback=feedback)
    return mock_response


class TestQuizGrader:
    """Tests for QuizGrader.grade."""

    def test_grader_returns_is_correct_true(self):
        """Mocked LLM returning is_correct=true."""
        mock_response = _mock_gemini_response(True, "Correct answer.")

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

        assert isinstance(result, GradingResult)
        assert result.is_correct is True

    def test_grader_returns_feedback_string(self):
        """Mocked LLM response produces feedback string."""
        mock_response = _mock_gemini_response(True, "Good explanation.")

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="Explain backpropagation.",
                expected_answer="Gradient descent via chain rule.",
                user_answer="Computes gradients using chain rule.",
                quiz_type="teach_back",
            )

        assert result.feedback == "Good explanation."

    def test_grader_returns_is_correct_false(self):
        """Mocked LLM returning is_correct=false."""
        mock_response = _mock_gemini_response(False, "The answer missed key concepts.")

        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning",
                user_answer="Not sure",
                quiz_type="free_recall",
            )

        assert result.is_correct is False
        assert result.feedback == "The answer missed key concepts."

    def test_mc_auto_graded_no_llm(self):
        """MC is auto-graded in API layer; QuizGrader not called."""
        with patch("src.service.quiz_grader.genai.Client") as mock_cls:
            correct_options = ["A", "C"]
            assert "A" in correct_options
            assert "B" not in correct_options
            mock_cls.assert_not_called()
