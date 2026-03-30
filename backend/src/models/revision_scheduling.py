"""Revision scheduling models: LessonRevisionRound, UserQuizRecall."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class LessonRevisionRound(Base):
    """Tracks one spaced-repetition round for a (user, lesson) pair."""

    __tablename__ = "lesson_revision_rounds"
    __table_args__ = (UniqueConstraint("username", "lesson_id", "round_num"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    round_num = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="open")
    due_at_lesson_count = Column(Integer, nullable=False, default=0)
    completed_at_lesson_count = Column(Integer, nullable=True)
    quizzes_in_round = Column(Integer, nullable=False, default=0)
    quizzes_answered = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())


class UserQuizRecall(Base):
    """Per-user, per-quiz MEMORIZE forgetting rate and review history."""

    __tablename__ = "user_quiz_recall"
    __table_args__ = (UniqueConstraint("username", "quiz_id"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("chapter_quizzes.id"), nullable=False)
    forgetting_rate = Column(Float, nullable=False, default=1.0)
    last_reviewed_lesson_count = Column(Integer, nullable=True)
    review_count = Column(Integer, nullable=False, default=0)
