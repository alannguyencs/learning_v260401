---
name: index-add
description: Register a NEW terminology note (terminologies/notes/{yymmdd}_{slug}.md) in the search index and the note↔terminology mapping so it becomes searchable via index-search and its terms appear in the master list. Wraps `python3 terminologies/index/bm25.py add <path>` plus `python3 terminologies/index/mapping.py sync <path>`. Use right after a new note is written — phrases like "add this note to the index", "register terminologies/notes/X.md", "index the new vLLM note", "make X searchable".
effort: low
---

# Index Add

Register a freshly-written terminology note so it appears in `index-search` results and its terminologies are mapped.

## What counts as a note

Only markdown files under `terminologies/notes/` (e.g. `terminologies/notes/260604_vllm.md`). The `terminology-create` skill writes these. Anything outside that folder is not a terminology note — don't index it here.

## Validation

1. File exists on disk (the script errors with `file not found` otherwise).
2. Path is under `terminologies/notes/` and ends in `.md`.
3. For the mapping to register terms, the note has a `### Key terminologies` section whose bullets use the `- **Term** — definition` form. If that section is missing, `bm25.py add` still works (full-text searchable) but `mapping.py sync` registers 0 terminologies — flag this, don't fail.

If the user gives only a filename or slug (e.g. "add the vllm note"), expand to the full `terminologies/notes/<file>.md` path and confirm before running.

## Run

Both steps — full-text index, then the terminology mapping:

```
python3 terminologies/index/bm25.py add terminologies/notes/<file>.md
python3 terminologies/index/mapping.py sync terminologies/notes/<file>.md
```

Success lines: `indexed terminologies/notes/<file>.md` and `synced …: N terminologies`. Errors:

- `file not found: …` — typo / not yet written.
- `no indexable tokens in …` — empty file or only stopwords; surface, don't retry.

If the path was already indexed, `add` overwrites the existing entry (same as `edit`) — that's fine, but prefer `index-update` for known re-indexes.

## Report

One line confirming both the search index and the mapping were updated, and how many terminologies were registered. Optionally suggest a verification search via `index-search`. On error, surface verbatim.

## Refusals

- Don't bulk-add by looping the notes folder — that's `bm25.py rebuild` + `mapping.py rebuild`, only on explicit request.
- Don't index files outside `terminologies/notes/`.
- Don't hand-edit `notes.json` or `notes_terminologies_mapping.json` — always go through the scripts.
