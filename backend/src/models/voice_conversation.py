"""Voice conversation model: VoiceConversationTurn.

One row per completed press-to-talk turn in a V2V Over Mode session. Because
Over Mode tears the Gemini Live session down after each turn, this table is the
only place history survives — the ``get_conversation_history`` tool reads it
back so the model can recall earlier turns.
"""

# pylint: disable=not-callable

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class VoiceConversationTurn(Base):
    """A single user/bot exchange within one voice session."""

    __tablename__ = "voice_conversation_turns"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    turn_index = Column(Integer, nullable=False)
    user_text = Column(Text, nullable=False)
    bot_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
