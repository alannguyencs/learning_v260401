"""Terminology note model: TerminologyNote.

Mirrors every file in ``terminologies/notes/`` so the voice tutor's
``search_notes`` tool can BM25-rank them from Postgres. ``term_freq`` and
``token_length`` are the precomputed per-document BM25 stats; corpus-level
stats are derived at query time (see ``service/notes_search.py``).
"""

# pylint: disable=not-callable

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class TerminologyNote(Base):
    """One row per ``terminologies/notes/*.md`` file, with BM25 stats."""

    __tablename__ = "terminology_notes"

    id = Column(Integer, primary_key=True, index=True)
    rel_path = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    raw_content = Column(Text, nullable=False)
    terminologies = Column(JSON, nullable=False, default=list)
    token_length = Column(Integer, nullable=False)
    term_freq = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
