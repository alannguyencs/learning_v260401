"""SlideChatService: uses Gemini API to answer user questions about slides."""

from pathlib import Path

from google import genai
from google.genai import types

from src.configs import settings

PROMPT_PATH = Path(__file__).parent.parent.parent / "resources" / "prompts" / "slide_chat.md"
MODEL = "gemini-2.5-flash"


class SlideChatService:
    """Answers user questions about slide content using Gemini."""

    @staticmethod
    def answer(
        slide_context: str,
        raw_content: str | None,
        recent_messages: list,
        user_message: str,
        slide_type: str = "chapter",
    ) -> str:
        """Build prompt with context and call Gemini for a free-text answer."""
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

        parts = [f"## Slide Type\n{slide_type}"]

        if raw_content:
            parts.append(f"## Lesson Source Material\n{raw_content}")

        parts.append(f"## Current Slide Content\n{slide_context}")

        if recent_messages:
            conversation = "\n".join(f"{msg.role}: {msg.content}" for msg in recent_messages)
            parts.append(f"## Recent Conversation\n{conversation}")

        parts.append(f"## User Question\n{user_message}")

        user_prompt = "\n\n".join(parts)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.GenerateContentConfig(temperature=0.3)
        response = client.models.generate_content(
            model=MODEL,
            contents=[full_prompt],
            config=config,
        )

        return response.text or ""
