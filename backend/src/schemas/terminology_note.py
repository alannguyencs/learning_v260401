"""Pydantic DTOs for terminology-note search."""

from pydantic import BaseModel


class NoteHit(BaseModel):
    """One BM25 search result returned to the caller (and the voice tool)."""

    rel_path: str
    title: str
    score: float
    content: str

    class Config:
        from_attributes = True
