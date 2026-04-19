"""Pydantic schemas for slide API requests and responses."""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


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
    correct_options: Optional[list] = None


class SlideResponse(BaseModel):
    """Response from GET /api/slides/current and POST /api/slides/forward|back."""

    slide_type: str
    chapter: Optional[ChapterSlide] = None
    quiz: Optional[QuizSlide] = None
    has_previous: bool = False
    feedback: Optional[dict] = None


class SlideForwardRequest(BaseModel):
    """Request body for POST /api/slides/forward."""

    book_id: Optional[str] = None
    mark_chapter_id: Optional[int] = None


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
    pre_evaluated: bool = False
    is_correct: Optional[bool] = None
    good_points: Optional[List[str]] = None
    bad_points: Optional[List[str]] = None


class QuizRespondResponse(BaseModel):
    """Response from POST /api/slides/quizzes/{id}/respond."""

    is_correct: Optional[bool] = None
    good_points: Optional[List[str]] = None
    bad_points: Optional[List[str]] = None
    round_done: bool


class SlideChatRequest(BaseModel):
    """Request body for POST /api/slides/chat."""

    slide_type: str
    chapter_id: Optional[int] = None
    quiz_id: Optional[int] = None
    message: str


class SlideChatResponse(BaseModel):
    """Response from POST /api/slides/chat."""

    response: str


class ChatMessageResponse(BaseModel):
    """A single chat message in history."""

    role: str
    content: str
    created_at: str


class LikeResponse(BaseModel):
    """Response from POST/DELETE /api/slides/quizzes/{id}/like."""

    liked: bool


class LikeListResponse(BaseModel):
    """Response from GET /api/slides/likes."""

    quiz_ids: List[int]
    chapter_ids: List[int] = []


class FavoriteQuiz(BaseModel):
    """A liked quiz rendered in the Dashboard Favorite tab (read-only preview)."""

    id: int
    chapter_id: int
    quiz_type: str
    question: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    expected_answer: Optional[str] = None
    lesson_id: int
    lesson_title: str
    book_id: str
    book_title: str
    section_name: Optional[str] = None
    quiz_take_away: Optional[str] = None
    quiz_metadata: Optional[dict] = None
    correct_options: Optional[list] = None
    liked_at: str


class FavoriteListResponse(BaseModel):
    """Response from GET /api/slides/liked-quizzes — newest like first."""

    quizzes: List[FavoriteQuiz]


class FavoriteChapter(BaseModel):
    """A liked chapter rendered in the Favorite tab (read-only preview)."""

    id: int
    lesson_id: int
    lesson_title: str
    lesson_index: int
    chapter_index: int
    book_id: str
    book_title: str
    title: str
    content: str


class LikedQuizItem(BaseModel):
    """Interleaved Favorite entry for a liked quiz."""

    type: Literal["quiz"] = "quiz"
    id: int
    liked_at: str
    quiz: FavoriteQuiz


class LikedChapterItem(BaseModel):
    """Interleaved Favorite entry for a liked chapter."""

    type: Literal["chapter"] = "chapter"
    id: int
    liked_at: str
    chapter: FavoriteChapter


class LikedItemsResponse(BaseModel):
    """Response from GET /api/slides/liked-items — newest like first, interleaved."""

    items: List[Union[LikedQuizItem, LikedChapterItem]] = Field(default_factory=list)
