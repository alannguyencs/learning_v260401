"""Content models: Book, Lesson, Chapter, ChapterQuiz."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class Book(Base):
    """Represents a learning book."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Lesson(Base):
    """Represents a lesson within a book, ordered by lesson_index."""

    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("book_id", "lesson_index"),)

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(String, ForeignKey("books.book_id"), nullable=False, index=True)
    lesson_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Chapter(Base):
    """Represents a chapter within a lesson, ordered by chapter_index."""

    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("lesson_id", "chapter_index"),)

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    chapter_index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ChapterQuiz(Base):
    """Represents a quiz question attached to a chapter."""

    __tablename__ = "chapter_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False, index=True)
    quiz_type = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    expected_answer = Column(Text)
    option_a = Column(Text)
    option_b = Column(Text)
    option_c = Column(Text)
    option_d = Column(Text)
    correct_options = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
