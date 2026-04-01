# Gemini Quiz Grader — Replace Anthropic with Gemini Structured Output

**Feature**: Replace the Anthropic-based QuizGrader with Google Gemini using structured output (response_schema)
**Plan Created:** 2026-04-01
**Status:** Plan
**Reference**:
- [Abstract — Content Upload](../abstract/content_upload.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- Reference implementation: `/Users/alan/Documents/delta/coach/backend/src/service/llm/llm_config.py`

---

## Problem Statement

1. The `QuizGrader` currently uses the Anthropic Claude API (`claude-haiku-4-5-20251001`) to grade open-ended quiz answers. The `ANTHROPIC_API_KEY` is not configured, so all free_recall, teach_back, and cloze grading fails with a `TypeError`.
2. The current implementation uses raw JSON string parsing (`json.loads(message.content[0].text)`) which is fragile — if the LLM returns malformed JSON or includes extra text, the grading crashes.
3. The project at `/Users/alan/Documents/delta/coach` has a proven pattern for Gemini with structured output via `response_schema` that guarantees valid JSON matching a Pydantic model. This project should adopt the same pattern.

---

## Proposed Solution

Replace the Anthropic SDK with the Google `genai` SDK using Gemini's native structured output feature:

- **Model**: `gemini-2.5-flash` (fast, cost-effective for grading)
- **Structured output**: `response_mime_type="application/json"` + `response_schema=GradingOutput` (Pydantic model) — the SDK guarantees the response conforms to the schema, eliminating JSON parsing errors
- **API key**: `GEMINI_API_KEY` loaded via `configs.py` settings
- **System prompt**: Kept as markdown file at `backend/resources/prompts/quiz_grader.md` — concatenated with the user message (Gemini does not have a separate `system` parameter in the same way, so the system prompt is prepended to `contents`)

```
QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
  │
  ├── Load system prompt from quiz_grader.md
  ├── Build user message: quiz_type + question + expected_answer + user_answer
  ├── Concatenate: full_prompt = system_prompt + "\n\n" + user_message
  │
  ├── client = genai.Client(api_key=settings.gemini_api_key)
  ├── config = GenerateContentConfig(
  │     response_mime_type="application/json",
  │     response_schema=GradingOutput,
  │     temperature=0.1,
  │   )
  │
  ├── response = client.models.generate_content(
  │     model="gemini-2.5-flash",
  │     contents=[full_prompt],
  │     config=config,
  │   )
  │
  └── Parse: response.parsed or GradingOutput.model_validate_json(response.text)
      → GradingResult(is_correct=..., feedback=...)
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `GradingResult` dataclass | `backend/src/service/quiz_grader.py` | Keep — same output contract |
| System prompt | `backend/resources/prompts/quiz_grader.md` | Keep — same grading logic |
| API endpoint call site | `backend/src/api/slides.py:97` | Keep — calls `QuizGrader.grade()` unchanged |
| MC auto-grading | `backend/src/api/slides.py:92-95` | Keep — no LLM needed |
| Test structure | `backend/tests/test_quiz_grader.py` | Keep — update mock targets |
| `.env` loading | `backend/src/configs.py` | Keep — add one new setting |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| LLM SDK | `anthropic` | `google-genai` |
| Model | `claude-haiku-4-5-20251001` | `gemini-2.5-flash` |
| API key | `ANTHROPIC_API_KEY` (implicit env var) | `GEMINI_API_KEY` (explicit in Settings) |
| Response parsing | `json.loads(message.content[0].text)` | `response.parsed` (native structured output) |
| Output schema | Inline JSON format instruction in prompt | Pydantic model as `response_schema` parameter |
| Client creation | `anthropic.Anthropic()` per call | `genai.Client(api_key=...)` per call |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
None.

#### To Add New

The grading flow after this plan:

```
[User] submits answer on /slides
  │
  ├── POST /api/slides/quizzes/{id}/respond
  │     quiz_type == "multiple_choice" → auto-grade (no LLM)
  │     quiz_type in (free_recall, teach_back, cloze) → QuizGrader.grade(...)
  │
  └── QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
        │
        ├── system_prompt = read quiz_grader.md
        ├── user_msg = "Quiz type: {}\nQuestion: {}\nExpected: {}\nStudent: {}"
        ├── full_prompt = system_prompt + "\n\n" + user_msg
        │
        ├── client = genai.Client(api_key=settings.gemini_api_key)
        ├── config = GenerateContentConfig(
        │     response_mime_type="application/json",
        │     response_schema=GradingOutput,
        │     temperature=0.1,
        │   )
        ├── response = client.models.generate_content(
        │     model="gemini-2.5-flash",
        │     contents=[full_prompt],
        │     config=config,
        │   )
        │
        └── return GradingResult(
              is_correct=response.parsed.is_correct,
              feedback=response.parsed.feedback,
            )
```

---

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no schema changes.

---

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no CRUD changes.

---

### Services

#### To Delete
None.

#### To Update

**`backend/src/service/quiz_grader.py`** — full rewrite of the `grade` method:

```python
"""QuizGrader: uses Gemini API to grade open-ended quiz answers."""

import json
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
```

Key changes from current:
- Replace `import anthropic` with `from google import genai` and `from google.genai import types`
- Add `GradingOutput` Pydantic model for structured output schema
- Use `genai.Client(api_key=settings.gemini_api_key)` instead of `anthropic.Anthropic()`
- Use `GenerateContentConfig` with `response_mime_type` and `response_schema` instead of raw `messages.create`
- Parse via `response.parsed` (native Pydantic object) with fallback to `model_validate_json`
- Concatenate system prompt + user message into single `contents` string
- Import `settings` from `src.configs` for the API key

#### To Add New
None — the `GradingOutput` Pydantic model is added inside the same file.

---

### API Endpoints

#### To Delete
None.

#### To Update
None — the API layer calls `QuizGrader.grade()` which keeps the same signature and return type.

#### To Add New
None.

---

### Testing

#### To Delete
None.

#### To Update

**`backend/tests/test_quiz_grader.py`** — update mock targets from Anthropic to Gemini:

```python
"""Unit tests for QuizGrader (LLM calls mocked)."""

from unittest.mock import MagicMock, patch

from src.service.quiz_grader import GradingOutput, GradingResult, QuizGrader


def _mock_gemini_response(is_correct: bool, feedback: str):
    """Build a mock Gemini generate_content response."""
    mock_response = MagicMock()
    mock_response.parsed = GradingOutput(
        is_correct=is_correct, feedback=feedback
    )
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
        mock_response = _mock_gemini_response(
            False, "The answer missed key concepts."
        )

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
```

#### To Add New

No new test files. Pre-commit loop:
1. Run `source venv/bin/activate && pre-commit run --all-files`
2. Fix any issues
3. Repeat until clean

---

### Frontend

#### To Delete
None.

#### To Update
None — the frontend is unchanged. It receives the same `{is_correct, feedback}` response from the API.

#### To Add New
None.

---

### Upload Script

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

---

### Documentation

#### Abstract (`docs/abstract/`)

No changes needed — the grading mechanism is an internal implementation detail not visible to users. The acceptance criteria and user flow remain the same.

#### Technical (`docs/technical/`)

**Update `docs/technical/slide_stack.md`**:
- **LLM Requests Layer**: Change model from `claude-haiku-4-5-20251001` to `gemini-2.5-flash`
- **LLM Requests Layer**: Update "System prompt" to note it's concatenated with user message (not a separate parameter)
- **LLM Requests Layer**: Add "Output schema" section describing the `GradingOutput` Pydantic model with `response_schema` parameter
- **Service Layer**: Update `QuizGrader` description to reference Gemini instead of Claude

---

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome E2E tests defined in `docs/chrome_test/gemini_quiz_grader.md`.

---

## Dependencies

- `google-genai>=0.1.0` — new pip dependency (replaces `anthropic`)
- `GEMINI_API_KEY` — must be set in `.env`
- `backend/src/configs.py` — needs `gemini_api_key` setting added
- `backend/requirements.txt` — needs `google-genai` added, `anthropic` removed

## Open Questions

None — the Gemini structured output pattern is well-proven in the delta/coach project.
