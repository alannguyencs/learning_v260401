"""QuizGrader: uses Gemini API to grade open-ended quiz answers."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.configs import settings

PROMPT_PATH = Path(__file__).parent.parent.parent / "resources" / "prompts" / "quiz_grader.md"
MODEL = "gemini-2.0-flash"
PASS_THRESHOLD = 0.66


class GradingOutput(BaseModel):
    """Structured output schema for Gemini quiz grading."""

    good_points: List[str] = Field(description="List of correct points in the student answer")
    bad_points: List[str] = Field(description="List of missing or incorrect points")


@dataclass
class GradingResult:
    """Result of grading an open-ended quiz answer."""

    is_correct: bool
    good_points: List[str] = field(default_factory=list)
    bad_points: List[str] = field(default_factory=list)


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

        total = len(parsed.good_points) + len(parsed.bad_points)
        is_correct = (len(parsed.good_points) / max(total, 1)) >= PASS_THRESHOLD

        return GradingResult(
            is_correct=is_correct,
            good_points=parsed.good_points,
            bad_points=parsed.bad_points,
        )
