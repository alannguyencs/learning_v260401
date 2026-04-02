"""Slide chat model: SlideChatMessage."""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class SlideChatMessage(Base):
    """Stores chat messages between user and AI on a specific slide."""

    __tablename__ = "slide_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    slide_identifier = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
