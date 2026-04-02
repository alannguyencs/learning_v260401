"""Pydantic schemas for content API requests and responses."""

from typing import List, Optional

from pydantic import BaseModel


class BookCreate(BaseModel):
    """Request schema for creating a book."""

    book_id: str
    title: str


class BookResponse(BaseModel):
    """Response schema for a book."""

    id: int
    book_id: str
    title: str

    class Config:
        """Pydantic configuration for ORM mode compatibility."""

        from_attributes = True


class LessonCreate(BaseModel):
    """Request schema for creating a lesson."""

    book_id: str
    lesson_index: int
    title: str
    raw_content: Optional[str] = None


class LessonResponse(BaseModel):
    """Response schema for a lesson."""

    id: int
    book_id: str
    lesson_index: int
    title: str

    class Config:
        """Pydantic configuration for ORM mode compatibility."""

        from_attributes = True


class ChapterCreate(BaseModel):
    """Request schema for creating a chapter."""

    lesson_id: int
    chapter_index: int
    title: str
    content: str


class ChapterResponse(BaseModel):
    """Response schema for a chapter."""

    id: int
    lesson_id: int
    chapter_index: int
    title: str

    class Config:
        """Pydantic configuration for ORM mode compatibility."""

        from_attributes = True


class QuizCreate(BaseModel):
    """Schema for a single quiz question in a batch upload."""

    quiz_type: str
    question: str
    expected_answer: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_options: Optional[List[str]] = None
    section_index: Optional[int] = None
    section_name: Optional[str] = None
    quiz_take_away: Optional[str] = None
    quiz_metadata: Optional[dict] = None


class QuizBatchCreate(BaseModel):
    """Request schema for batch uploading quizzes for a chapter."""

    chapter_id: int
    quizzes: List[QuizCreate]


class QuizBatchResponse(BaseModel):
    """Response schema for batch quiz upload."""

    inserted: int


class ChapterSummary(BaseModel):
    """Summary of a chapter with quiz count (used in book structure)."""

    id: int
    chapter_index: int
    title: str
    quiz_count: int


class LessonStructure(BaseModel):
    """Lesson with its chapters (used in book structure)."""

    id: int
    lesson_index: int
    title: str
    chapters: List[ChapterSummary]


class BookStructureResponse(BaseModel):
    """Full hierarchical structure of a book."""

    book_id: str
    title: str
    lessons: List[LessonStructure]
