"""QuizGrader: uses Claude API to grade open-ended quiz answers."""

import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

PROMPT_PATH = Path(__file__).parent.parent.parent / "resources" / "prompts" / "quiz_grader.md"
MODEL = "claude-haiku-4-5-20251001"


@dataclass
class GradingResult:
    """Result of grading an open-ended quiz answer."""

    is_correct: bool
    feedback: str


class QuizGrader:
    """Grades open-ended quiz answers using the Claude API."""

    @staticmethod
    def grade(
        question: str,
        expected_answer: str,
        user_answer: str,
        quiz_type: str,
    ) -> GradingResult:
        """
        Call Claude API with a structured grading prompt.

        Model: claude-haiku-4-5-20251001 (fast, cost-effective for grading).
        Returns GradingResult with is_correct and feedback.
        """
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_message = (
            f"Quiz type: {quiz_type}\n"
            f"Question: {question}\n"
            f"Expected answer: {expected_answer}\n"
            f"Student answer: {user_answer}"
        )

        client = anthropic.Anthropic()
        message = client.messages.create(
            model=MODEL,
            max_tokens=256,
            temperature=0.1,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text
        parsed = json.loads(raw)
        return GradingResult(
            is_correct=bool(parsed["is_correct"]),
            feedback=str(parsed["feedback"]),
        )
