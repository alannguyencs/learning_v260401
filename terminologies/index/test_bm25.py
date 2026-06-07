"""End-to-end test for terminologies/index/bm25.py.

Builds a tiny notes corpus in a temp dir, exercises add / edit / remove /
search / rebuild, and asserts BM25 ranks notes the way intuition expects.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import bm25


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    """Stand up a fake project root with three terminology notes."""
    root = tmp_path / "proj"
    notes = root / "terminologies" / "notes"
    notes.mkdir(parents=True)
    (root / "terminologies" / "glossary").mkdir(parents=True)
    index_dir = root / "terminologies" / "index"
    index_dir.mkdir(parents=True)

    (notes / "alpha.md").write_text("# Alpha\n\nApples and oranges. Apples again.\n")
    (notes / "beta.md").write_text("# Beta\n\nBananas and oranges only.\n")
    (notes / "gamma.md").write_text("# Gamma\n\nCarrots, celery, and cabbage.\n")

    monkeypatch.setattr(bm25, "PROJECT_ROOT", root)
    monkeypatch.setattr(bm25, "INDEX_DIR", index_dir)
    return root


def _rel(root: Path, name: str) -> str:
    return (root / "terminologies" / "notes" / name).relative_to(root).as_posix()


def test_tokenize_strips_markdown_links_and_stopwords():
    tokens = bm25.tokenize("See [the docs](https://example.com/x) for more.")
    assert "docs" in tokens
    assert "example" not in tokens
    assert "the" not in tokens


def test_rebuild_indexes_all_notes(fake_project):
    root = fake_project
    bm25.main(["rebuild"])
    idx = bm25.BM25Index.load()
    assert set(idx.documents) == {
        _rel(root, "alpha.md"),
        _rel(root, "beta.md"),
        _rel(root, "gamma.md"),
    }


def test_search_ranks_expected_note_first(fake_project):
    root = fake_project
    bm25.main(["rebuild"])
    idx = bm25.BM25Index.load()

    assert idx.search("apples", top_k=3)[0][0] == _rel(root, "alpha.md")
    assert idx.search("bananas", top_k=3)[0][0] == _rel(root, "beta.md")
    assert idx.search("carrots celery", top_k=3)[0][0] == _rel(root, "gamma.md")


def test_add_edit_remove_round_trip(fake_project):
    root = fake_project
    rel = _rel(root, "alpha.md")

    bm25.main(["add", rel])
    idx = bm25.BM25Index.load()
    assert rel in idx.documents
    original_len = idx.documents[rel]["length"]

    (root / rel).write_text(
        (root / rel).read_text() + "\nMore apples and pears here.\n"
    )
    bm25.main(["edit", rel])
    idx = bm25.BM25Index.load()
    assert idx.documents[rel]["length"] > original_len
    assert "pears" in idx.documents[rel]["term_freq"]

    bm25.main(["remove", rel])
    idx = bm25.BM25Index.load()
    assert rel not in idx.documents


def test_remove_unknown_path_errors(fake_project):
    root = fake_project
    bm25.main(["rebuild"])
    with pytest.raises(SystemExit):
        bm25.main(["remove", _rel(root, "does_not_exist.md")])


def test_search_empty_index_returns_no_hits(fake_project):
    idx = bm25.BM25Index.load()
    assert idx.search("anything") == []


def test_terminologies_corpus_is_separate_from_notes(fake_project):
    root = fake_project
    glossary = root / "terminologies" / "glossary"
    (glossary / "kv_cache.md").write_text("# KV cache\n\nstored key value vectors\n")
    (glossary / "attention.md").write_text("# Attention\n\nlook back at tokens\n")

    bm25.main(["rebuild", "--corpus", "terminologies"])
    bm25.main(["rebuild"])  # notes corpus, default

    # Each corpus has its own on-disk index file.
    assert (root / "terminologies" / "index" / "terminologies.json").exists()
    assert (root / "terminologies" / "index" / "notes.json").exists()

    # Searching the terminologies corpus returns glossary pages, ranked.
    term_idx = bm25.BM25Index.load(bm25._index_path("terminologies"))
    hits = term_idx.search("key value cache", top_k=2)
    assert hits[0][0] == "terminologies/glossary/kv_cache.md"

    # The notes corpus is untouched by the terminologies rebuild.
    notes_idx = bm25.BM25Index.load(bm25._index_path("notes"))
    assert all("notes/" in p for p in notes_idx.documents)
