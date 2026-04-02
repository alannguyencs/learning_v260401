"""Unit tests for SlideChatService (LLM calls mocked)."""

from unittest.mock import MagicMock, patch

from src.service.slide_chat_service import RAW_CONTENT_MAX_CHARS, SlideChatService


def _mock_gemini_response(text: str):
    """Build a mock Gemini generate_content response."""
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


class TestSlideChatService:
    """Tests for SlideChatService.answer."""

    @patch("src.service.slide_chat_service.genai.Client")
    def test_answer_includes_slide_context(self, mock_cls):
        """Prompt sent to Gemini contains the slide context."""
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = _mock_gemini_response("OK")

        SlideChatService.answer("Chapter content here", None, [], "What is this?")

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"][0] if "contents" in call_args[1] else call_args[0][1][0]
        assert "Chapter content here" in prompt

    @patch("src.service.slide_chat_service.genai.Client")
    def test_answer_handles_null_raw_content(self, mock_cls):
        """Service works when raw_content is None."""
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = _mock_gemini_response("Response")

        result = SlideChatService.answer("Slide text", None, [], "Question?")
        assert result == "Response"

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"][0] if "contents" in call_args[1] else call_args[0][1][0]
        assert "Lesson Source Material" not in prompt

    @patch("src.service.slide_chat_service.genai.Client")
    def test_answer_truncates_long_raw_content(self, mock_cls):
        """Raw content longer than limit is truncated."""
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = _mock_gemini_response("OK")

        long_content = "x" * (RAW_CONTENT_MAX_CHARS + 1000)
        SlideChatService.answer("Slide", long_content, [], "Q?")

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"][0] if "contents" in call_args[1] else call_args[0][1][0]
        assert "x" * RAW_CONTENT_MAX_CHARS in prompt
        assert "x" * (RAW_CONTENT_MAX_CHARS + 1) not in prompt

    @patch("src.service.slide_chat_service.genai.Client")
    def test_answer_includes_recent_messages(self, mock_cls):
        """Prompt includes recent conversation history."""
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = _mock_gemini_response("OK")

        msg1 = MagicMock()
        msg1.role = "user"
        msg1.content = "Previous question"
        msg2 = MagicMock()
        msg2.role = "assistant"
        msg2.content = "Previous answer"

        SlideChatService.answer("Slide", None, [msg1, msg2], "Follow up?")

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"][0] if "contents" in call_args[1] else call_args[0][1][0]
        assert "Previous question" in prompt
        assert "Previous answer" in prompt
