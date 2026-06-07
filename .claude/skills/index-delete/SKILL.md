---
name: index-delete
description: Remove a terminology note from the search index and the note↔terminology mapping so it no longer appears in index-search results or the master list. Wraps `python3 terminologies/index/bm25.py remove <path>` plus `python3 terminologies/index/mapping.py remove <path>`. **Does NOT delete the underlying .md file on disk** — only the index/mapping entries. Use when a note was deleted, retired, or wrongly indexed — phrases like "drop X from the index", "unindex the vllm note", "deregister X".
effort: low
---

# Index Delete

Remove a single note from both the BM25 index and the note↔terminology mapping. **The `.md` file on disk is untouched** — only the index entries. If the user wants to delete the file too, that's a separate `git rm` / `rm`.

## Disambiguation

If the user says *"delete the vllm note"* (ambiguous between deleting the file and deleting the index entry), **ask** which they mean before running. This skill only removes index/mapping entries.

## Validation

1. Path is under `terminologies/notes/` and ends in `.md`.
2. The note is currently in the index / mapping — otherwise the scripts error with `not in index: <path>` / `not in mapping: <path>`. If unsure, confirm via `index-search` or `index-mapping list` first.

## Run

Remove from the full-text index and the mapping (regenerates `index.md` automatically):

```
python3 terminologies/index/bm25.py remove terminologies/notes/<file>.md
python3 terminologies/index/mapping.py remove terminologies/notes/<file>.md
```

Success lines: `removed terminologies/notes/<file>.md` and `removed … from mapping`. Errors:

- `not in index: <path>` / `not in mapping: <path>` — already removed, or path typo. Surface; don't retry.

If only one of the two stores has the entry (e.g. the note had no `### Key terminologies` section, so it was never in the mapping), the missing-store command will error — run the other, and report the partial state plainly rather than treating it as a failure.

## Report

One line confirming the entries were removed. **If the underlying `.md` file still exists on disk, say so explicitly** so the user can decide whether to delete the file too. Note that any terminology unique to this note has now dropped out of the master list, while shared terms remain.

## Refusals

- Don't touch the file on disk — only the index and mapping.
- Don't run `rebuild` (that's the opposite of what was asked).
- Don't bulk-delete by looping.
- Don't hand-edit `notes.json` or `notes_terminologies_mapping.json`.
