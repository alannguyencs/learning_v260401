"""Slide position models: UserSlidePosition, SlideHistory."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.types import JSON
from sqlalchemy.sql import func

from ..database import Base


class UserSlidePosition(Base):
    """Current slide position for each user (one row per user)."""

    __tablename__ = "slide_position"

    username = Column(String, ForeignKey("users.username"), primary_key=True)
    slide_type = Column(String, nullable=False)
    slide_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, nullable=True)
    round_num = Column(Integer, nullable=True)
    feedback_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class SlideHistory(Base):
    """Ordered history stack for back/forward navigation."""

    __tablename__ = "slide_history"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    slide_type = Column(String, nullable=False)
    slide_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, nullable=True)
    round_num = Column(Integer, nullable=True)
    feedback_json = Column(JSON, nullable=True)
    direction = Column(String, nullable=False, server_default="back")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
