"""Slide like model: UserSlideLike (polymorphic over quizzes and chapters)."""

# pylint: disable=not-callable

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from ..database import Base


class UserSlideLike(Base):
    """Per-user like of either a quiz or a chapter.

    Exactly one of `quiz_id` / `chapter_id` is set per row (DB CHECK constraint).
    Quiz likes also trigger a forgetting-rate boost; chapter likes are pure
    bookmarks and do not affect the slide selector.
    """

    __tablename__ = "user_slide_like"
    __table_args__ = (
        UniqueConstraint("username", "quiz_id"),
        UniqueConstraint("username", "chapter_id"),
        CheckConstraint(
            "(quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL)",
            name="usl_exactly_one_target",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("chapter_quizzes.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    liked_at = Column(DateTime, nullable=False, server_default=func.now())
