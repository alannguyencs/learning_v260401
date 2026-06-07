---
name: index-update
description: Refresh an already-indexed terminology note — re-reads the file from disk and overwrites its BM25 entry with a freshly-tokenized version, then re-syncs its terminologies. Wraps `python3 terminologies/index/bm25.py edit <path>` plus `python3 terminologies/index/mapping.py sync <path>`. Use when a note already in the index was edited — phrases like "refresh the vllm note", "re-index X", "the note changed, sync the index", "update X in the index".
effort: low
---

# Index Update

Re-tokenize an already-indexed note so its BM25 entry and terminology mapping reflect current content.

## Validation

1. File exists on disk under `terminologies/notes/`.
2. (Recommended) the path is already present in `terminologies/index/notes.json`. The underlying `edit` succeeds either way, but if the path isn't there yet the user probably wanted `index-add` — flag it, don't refuse.

## Run

Refresh the full-text entry, then re-derive its terminologies (the `### Key terminologies` section may have changed):

```
python3 terminologies/index/bm25.py edit terminologies/notes/<file>.md
python3 terminologies/index/mapping.py sync terminologies/notes/<file>.md
```

Success lines: `updated terminologies/notes/<file>.md` and `synced …: N terminologies`. Errors:

- `file not found: …` — typo or file moved.
- `no indexable tokens in …` — empty / stopword-only; surface, don't retry.

`mapping.py sync` re-reads the section: terms added to the note are registered, terms removed drop out of the master list (`index.md` is regenerated automatically). If editing the note removed the entire `### Key terminologies` section, sync registers 0 terms and drops the note from the mapping — call that out.

## Report

One line confirming the entry was refreshed and the new terminology count. Optionally suggest a verification search via `index-search`.

## Refusals

- Don't bulk-update by looping — that's `rebuild`, only on explicit request.
- Don't fall back to other commands silently on error.
- Don't hand-edit `notes.json` or `notes_terminologies_mapping.json`.
