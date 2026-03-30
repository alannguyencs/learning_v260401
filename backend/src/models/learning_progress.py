"""Learning progress models: UserChapterProgress, UserLessonCount."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class UserChapterProgress(Base):
    """Records when a user marks a chapter as learnt."""

    __tablename__ = "user_chapter_progress"
    __table_args__ = (UniqueConstraint("username", "chapter_id"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    learnt_at = Column(DateTime, nullable=False, server_default=func.now())


class UserLessonCount(Base):
    """Tracks the total number of fully-learnt lessons per user."""

    __tablename__ = "user_lesson_count"

    username = Column(String, ForeignKey("users.username"), primary_key=True)
    total_lessons_learnt = Column(Integer, nullable=False, default=0)
