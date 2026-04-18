"""Slide like model: UserSlideLike."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from ..database import Base


class UserSlideLike(Base):
    """Per-user quiz like; drives the filled/outline heart UI."""

    __tablename__ = "user_slide_like"
    __table_args__ = (UniqueConstraint("username", "quiz_id"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("chapter_quizzes.id"), nullable=False)
    liked_at = Column(DateTime, nullable=False, server_default=func.now())
