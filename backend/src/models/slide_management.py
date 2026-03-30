"""Slide management models: QuizSkipLog."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class QuizSkipLog(Base):
    """Records when a user skips a quiz for later resurface (Tier 3)."""

    __tablename__ = "quiz_skip_log"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("chapter_quizzes.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    round_num = Column(Integer, nullable=False)
    skipped_at = Column(DateTime, nullable=False, server_default=func.now())
