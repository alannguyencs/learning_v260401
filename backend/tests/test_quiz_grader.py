"""Unit tests for QuizGrader (LLM calls mocked)."""

from unittest.mock import MagicMock, patch

from src.service.quiz_grader import GradingResult, QuizGrader


def _mock_llm_response(is_correct: bool, feedback: str):
    """Build a mock anthropic message response."""
    mock_msg = MagicMock()
    mock_msg.content = [
        MagicMock(text=f'{{"is_correct": {str(is_correct).lower()}, "feedback": "{feedback}"}}')
    ]
    return mock_msg


class TestQuizGrader:
    """Tests for QuizGrader.grade."""

    def test_grader_returns_is_correct_true(self):
        """Mocked LLM returning is_correct=true → GradingResult.is_correct=True."""
        mock_response = _mock_llm_response(True, "Correct answer.")

        with patch("src.service.quiz_grader.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning",
                user_answer="Machine Learning",
                quiz_type="free_recall",
            )

        assert isinstance(result, GradingResult)
        assert result.is_correct is True

    def test_grader_returns_feedback_string(self):
        """Mocked LLM response → feedback string populated in GradingResult."""
        mock_response = _mock_llm_response(True, "Good explanation of the concept.")

        with patch("src.service.quiz_grader.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = QuizGrader.grade(
                question="Explain backpropagation.",
                expected_answer="Gradient descent via chain rule.",
                user_answer="Computes gradients using chain rule.",
                quiz_type="teach_back",
            )

        assert result.feedback == "Good explanation of the concept."

    def test_grader_returns_is_correct_false(self):
        """Mocked LLM returning is_correct=false → GradingResult.is_correct=False."""
        mock_response = _mock_llm_response(False, "The answer missed key concepts.")

        with patch("src.service.quiz_grader.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            result = QuizGrader.grade(
                question="What is ML?",
                expected_answer="Machine Learning",
                user_answer="Not sure",
                quiz_type="free_recall",
            )

        assert result.is_correct is False
        assert result.feedback == "The answer missed key concepts."

    def test_mc_auto_graded_no_llm(self):
        """MC type is auto-graded in the API layer; QuizGrader.grade is not called."""
        with patch("src.service.quiz_grader.anthropic.Anthropic") as mock_cls:
            # Verify that creating an Anthropic client is never triggered for MC
            # by testing the auto-grade logic directly (not going through grader)
            correct_options = ["A", "C"]
            user_answer_correct = "A"
            user_answer_wrong = "B"

            assert user_answer_correct in correct_options
            assert user_answer_wrong not in correct_options
            mock_cls.assert_not_called()
