"""Pydantic schemas for slide API requests and responses."""

from typing import Optional

from pydantic import BaseModel


class ChapterSlide(BaseModel):
    """Chapter slide data returned to the client."""

    id: int
    lesson_id: int
    book_id: str
    book_title: str
    lesson_title: str
    lesson_index: int
    chapter_index: int
    title: str
    content: str


class QuizSlide(BaseModel):
    """Quiz slide data returned to the client."""

    id: int
    chapter_id: int
    quiz_type: str
    question: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    expected_answer: Optional[str] = None
    round_num: int
    lesson_id: int
    lesson_title: str
    book_title: str
    section_name: Optional[str] = None
    quiz_take_away: Optional[str] = None
    quiz_metadata: Optional[dict] = None


class SlideResponse(BaseModel):
    """Response from GET /api/slides/next."""

    slide_type: str
    chapter: Optional[ChapterSlide] = None
    quiz: Optional[QuizSlide] = None


class ChapterLearntResponse(BaseModel):
    """Response from POST /api/slides/chapters/{id}/learnt."""

    lesson_fully_learnt: bool
    lesson_count: int


class QuizRespondRequest(BaseModel):
    """Request body for POST /api/slides/quizzes/{id}/respond."""

    round_num: int
    lesson_id: int
    user_answer: str
    is_skip: bool


class QuizRespondResponse(BaseModel):
    """Response from POST /api/slides/quizzes/{id}/respond."""

    is_correct: Optional[bool] = None
    feedback: Optional[str] = None
    round_done: bool
