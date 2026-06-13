"""CRUD operations for terminology notes (the BM25 search corpus)."""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.terminology_note import TerminologyNote


def list_all(db: Session) -> List[TerminologyNote]:
    """Every indexed note. The whole corpus is loaded for in-memory BM25."""
    return db.query(TerminologyNote).order_by(TerminologyNote.rel_path.asc()).all()


def get_by_rel_path(db: Session, rel_path: str) -> Optional[TerminologyNote]:
    """One note by its project-root-relative path, or None."""
    return db.query(TerminologyNote).filter(TerminologyNote.rel_path == rel_path).first()


def upsert(
    db: Session,
    *,
    rel_path: str,
    title: str,
    raw_content: str,
    terminologies: List[str],
    token_length: int,
    term_freq: Dict[str, int],
) -> TerminologyNote:
    """Insert a note or overwrite the existing row with the same rel_path."""
    note = get_by_rel_path(db, rel_path)
    if note is None:
        note = TerminologyNote(rel_path=rel_path)
        db.add(note)
    note.title = title
    note.raw_content = raw_content
    note.terminologies = terminologies
    note.token_length = token_length
    note.term_freq = term_freq
    db.commit()
    db.refresh(note)
    return note


def delete_by_rel_path(db: Session, rel_path: str) -> bool:
    """Delete a note by rel_path. Returns True if a row was removed."""
    note = get_by_rel_path(db, rel_path)
    if note is None:
        return False
    db.delete(note)
    db.commit()
    return True
