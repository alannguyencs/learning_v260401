"""Tests for BM25 note search (service/notes_search.py)."""

from src.crud import crud_terminology_notes as crud
from src.service.notes_search import search_notes
from src.utils import bm25_core


def _add(db, rel_path, title, content):
    """Insert a note row with BM25 stats derived from its content."""
    tokens = bm25_core.tokenize(content)
    return crud.upsert(
        db,
        rel_path=rel_path,
        title=title,
        raw_content=content,
        terminologies=[],
        token_length=len(tokens),
        term_freq=bm25_core.term_freq(tokens),
    )


def test_ranks_relevant_note_first(db_session):
    _add(
        db_session,
        "terminologies/notes/attention.md",
        "Attention",
        "Attention lets each token look back at earlier tokens via query key "
        "value vectors and a softmax. Attention is the core transformer block.",
    )
    _add(
        db_session,
        "terminologies/notes/cooking.md",
        "Cooking",
        "A recipe for pasta with tomato, basil, and olive oil in the kitchen.",
    )

    hits = search_notes(db_session, "transformer attention softmax", top_k=2)

    assert hits, "expected at least one hit"
    assert hits[0].rel_path == "terminologies/notes/attention.md"
    assert hits[0].title == "Attention"
    assert hits[0].score > 0
    assert "Attention" in hits[0].content


def test_top_k_limits_results(db_session):
    for i in range(5):
        _add(
            db_session,
            f"terminologies/notes/n{i}.md",
            f"Note {i}",
            "attention transformer token softmax vectors",
        )

    hits = search_notes(db_session, "attention", top_k=3)

    assert len(hits) == 3


def test_empty_query_returns_no_hits(db_session):
    _add(db_session, "terminologies/notes/a.md", "A", "attention transformer token")

    assert search_notes(db_session, "") == []
    assert search_notes(db_session, "   ") == []


def test_no_match_returns_empty(db_session):
    _add(db_session, "terminologies/notes/a.md", "A", "attention transformer token")

    assert search_notes(db_session, "zzzz nonexistent gibberish") == []


def test_empty_corpus_returns_empty(db_session):
    assert search_notes(db_session, "attention") == []
