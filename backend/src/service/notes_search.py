"""BM25 keyword search over the terminology-note corpus.

Loads the whole corpus from Postgres (small — tens to low hundreds of notes),
computes corpus stats in memory, and ranks notes by BM25. This is Tool #2 of
the voice tutor: ``search_notes`` hands the model the top notes' content as
grounding. Keeping the scoring in Python (not Postgres FTS) keeps the same code
path working against SQLite in tests.
"""

from typing import List

from sqlalchemy.orm import Session

from src.crud import crud_terminology_notes as crud
from src.schemas.terminology_note import NoteHit
from src.utils import bm25_core

# Notes are small (~3 KB); cap the grounding text handed back per hit so a
# future oversized note can't blow up a tool response.
MAX_CONTENT_CHARS = 6000


def search_notes(db: Session, query: str, top_k: int = 3) -> List[NoteHit]:
    """Return the top-k terminology notes for ``query``, ranked by BM25."""
    rows = crud.list_all(db)
    if not rows:
        return []
    documents = {
        row.rel_path: {"length": row.token_length, "term_freq": row.term_freq} for row in rows
    }
    ranked = bm25_core.bm25_scores(query, documents)[:top_k]
    by_path = {row.rel_path: row for row in rows}
    hits: List[NoteHit] = []
    for rel_path, score in ranked:
        row = by_path[rel_path]
        hits.append(
            NoteHit(
                rel_path=rel_path,
                title=row.title,
                score=round(score, 4),
                content=row.raw_content[:MAX_CONTENT_CHARS],
            )
        )
    return hits
