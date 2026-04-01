"""QuizGrader: uses Gemini API to grade open-ended quiz answers."""

from dataclasses import dataclass
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.configs import settings

PROMPT_PATH = Path(__file__).parent.parent.parent / "resources" / "prompts" / "quiz_grader.md"
MODEL = "gemini-2.5-flash"


class GradingOutput(BaseModel):
    """Structured output schema for Gemini quiz grading."""

    is_correct: bool = Field(description="Whether the student answer is correct")
    feedback: str = Field(description="One sentence explaining the grade")


@dataclass
class GradingResult:
    """Result of grading an open-ended quiz answer."""

    is_correct: bool
    feedback: str


class QuizGrader:
    """Grades open-ended quiz answers using the Gemini API."""

    @staticmethod
    def grade(
        question: str,
        expected_answer: str,
        user_answer: str,
        quiz_type: str,
    ) -> GradingResult:
        """Call Gemini API with structured output for grading."""
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_message = (
            f"Quiz type: {quiz_type}\n"
            f"Question: {question}\n"
            f"Expected answer: {expected_answer}\n"
            f"Student answer: {user_answer}"
        )
        full_prompt = f"{system_prompt}\n\n{user_message}"

        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GradingOutput,
            temperature=0.1,
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=[full_prompt],
            config=config,
        )

        if response.parsed:
            parsed = response.parsed
        else:
            parsed = GradingOutput.model_validate_json(response.text)

        return GradingResult(
            is_correct=parsed.is_correct,
            feedback=parsed.feedback,
        )
