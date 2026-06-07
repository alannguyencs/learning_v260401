"""End-to-end test for terminologies/index/mapping.py.

Builds a couple of fake notes with '### Key terminologies' sections and
checks parsing, the two-way lookup, the master list, and index.md output.
"""

from __future__ import annotations

import pytest

import mapping


NOTE_A = """# vLLM

### Key terminologies

- **Large Language Model (LLM)** — a network that generates text.
- **KV cache (Key–Value cache)** — stored attention vectors.
- **vLLM** — a serving engine.

### How these terms are related

1. blah → blah.
"""

NOTE_B = """# Transformers

### Key terminologies

- **Attention** — looking back at tokens.
- **KV cache (Key–Value cache)** — stored attention vectors.

### Concrete example

code here.
"""


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    notes = root / "terminologies" / "notes"
    notes.mkdir(parents=True)
    index_dir = root / "terminologies" / "index"
    index_dir.mkdir(parents=True)

    (notes / "260604_vllm.md").write_text(NOTE_A)
    (notes / "260605_transformers.md").write_text(NOTE_B)

    monkeypatch.setattr(mapping, "PROJECT_ROOT", root)
    monkeypatch.setattr(mapping, "INDEX_DIR", index_dir)
    return root


def test_parse_terminologies_reads_only_key_section(fake_project):
    terms = mapping.parse_terminologies(
        "terminologies/notes/260604_vllm.md"
    )
    assert terms == [
        "Large Language Model (LLM)",
        "KV cache (Key–Value cache)",
        "vLLM",
    ]


def test_rebuild_builds_two_way_index_and_master_list(fake_project):
    mapping.main(["rebuild"])
    m = mapping.NotesTerminologyMapping.load()

    # note -> terminologies
    assert "Attention" in m.terminologies_for(
        "terminologies/notes/260605_transformers.md"
    )
    # terminology -> notes (shared term spans both notes)
    assert m.notes_for("KV cache (Key–Value cache)") == [
        "terminologies/notes/260604_vllm.md",
        "terminologies/notes/260605_transformers.md",
    ]
    # master list is sorted case-insensitively and de-duplicated
    assert m.terminologies == [
        "Attention",
        "KV cache (Key–Value cache)",
        "Large Language Model (LLM)",
        "vLLM",
    ]


def test_rebuild_writes_index_md(fake_project):
    mapping.main(["rebuild"])
    index_md = (
        fake_project / "terminologies" / "index" / "index.md"
    ).read_text()
    assert "# Terminologies Index" in index_md
    assert "**Attention**" in index_md
    assert "`260604_vllm.md`" in index_md


def test_sync_single_note_updates_mapping(fake_project):
    mapping.main(["rebuild"])
    note = fake_project / "terminologies" / "notes" / "260605_transformers.md"
    note.write_text(NOTE_B + "\n- not in a key section **Ignored** —\n")
    mapping.main(["sync", "terminologies/notes/260605_transformers.md"])

    m = mapping.NotesTerminologyMapping.load()
    assert "Ignored" not in m.terminologies
    assert "Attention" in m.terminologies


def test_parse_terminology_entries_captures_definitions(fake_project):
    entries = mapping.parse_terminology_entries(
        "terminologies/notes/260604_vllm.md"
    )
    assert entries[0] == (
        "Large Language Model (LLM)",
        "a network that generates text.",
    )


def test_rebuild_writes_one_standalone_glossary_page_per_term(fake_project):
    mapping.main(["rebuild"])
    glossary = fake_project / "terminologies" / "glossary"
    names = sorted(p.name for p in glossary.glob("*.md"))
    assert names == [
        "attention.md",
        "kv_cache_key_value_cache.md",
        "large_language_model_llm.md",
        "vllm.md",
    ]
    # Pages are standalone: title + definition, no note link, no marker.
    kv = (glossary / "kv_cache_key_value_cache.md").read_text()
    assert kv.startswith("# KV cache (Key–Value cache)")
    assert "stored attention vectors." in kv
    assert "../notes/" not in kv
    assert "mapping.py" not in kv
    assert "260604_vllm.md" not in kv


def test_glossary_prunes_stale_pages(fake_project):
    mapping.main(["rebuild"])
    glossary = fake_project / "terminologies" / "glossary"
    # Remove a note, re-sync: terms unique to it lose their glossary page.
    mapping.main(["remove", "terminologies/notes/260604_vllm.md"])
    assert not (glossary / "large_language_model_llm.md").exists()
    assert (glossary / "attention.md").exists()  # still defined elsewhere


def test_glossary_folder_is_generator_owned(fake_project):
    """The folder holds only generated term pages — a stray .md is pruned."""
    mapping.main(["rebuild"])
    glossary = fake_project / "terminologies" / "glossary"
    (glossary / "stray.md").write_text("# not a term\n")
    mapping.main(["glossary"])
    assert not (glossary / "stray.md").exists()


def test_remove_note_from_mapping(fake_project):
    mapping.main(["rebuild"])
    mapping.main(["remove", "terminologies/notes/260604_vllm.md"])
    m = mapping.NotesTerminologyMapping.load()
    assert "terminologies/notes/260604_vllm.md" not in m.notes
    # A term unique to the removed note is gone; a shared term survives.
    assert "Large Language Model (LLM)" not in m.terminologies
    assert "KV cache (Key–Value cache)" in m.terminologies


def test_remove_unknown_note_errors(fake_project):
    mapping.main(["rebuild"])
    with pytest.raises(SystemExit):
        mapping.main(["remove", "terminologies/notes/nope.md"])


def test_load_missing_mapping_is_empty(fake_project):
    m = mapping.NotesTerminologyMapping.load()
    assert m.terminologies == []
    assert m.notes == []
