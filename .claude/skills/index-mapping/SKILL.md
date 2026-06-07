---
name: index-mapping
description: Query and maintain the note ↔ terminology mapping at terminologies/index/notes_terminologies_mapping.json — look up which terminologies a note defines, which notes define a given terminology, list the whole master list of terminologies, or re-sync a note's terms from its `### Key terminologies` section. Wraps `terminologies/index/mapping.py`. Use when the user wants to query or repair the relationship between notes and the terminologies they define.
effort: low
---

# Index Mapping

Bidirectional lookup + maintenance for the note ↔ terminology mapping. Unlike a hand-wired edge table, this mapping is **derived by parsing each note's `### Key terminologies` section**, so there is no "add edge" — you `sync` a note and its terms are re-derived.

## Operations

| User intent | Op | Command |
|-------------|----|---------|
| "what terminologies does note X define?" / "list the terms in X" | terminologies | `mapping.py terminologies <note>` |
| "which notes define terminology Y?" / "where is Y explained?" | notes | `mapping.py notes "<terminology>"` |
| "list all terminologies" / "show the master list" | list | `mapping.py list` |
| "regenerate the glossary pages" | glossary | `mapping.py glossary` |
| "re-sync X" / "X's key-terms section changed" | sync | `mapping.py sync <note>` |
| "drop X from the mapping" | remove | `mapping.py remove <note>` |
| "rebuild the whole mapping from disk" | rebuild | `mapping.py rebuild` |

`sync` / `remove` / `rebuild` also regenerate two artifacts: the master list at `terminologies/index/index.md` **and** the per-term pages under `terminologies/glossary/` (one **standalone** `<slug>.md` per terminology — just the term title + its definition, with **no link back to any note**; the note ↔ terminology relationship lives only in `notes_terminologies_mapping.json`). The standalone `glossary` op regenerates only the glossary pages — use it if those got out of sync without a mapping change. The glossary folder is generator-owned: pages for removed terms and any stray `.md` are pruned, so don't keep hand-written files there.

For full-text search of note *bodies* by topic, use `index-search` (BM25). For registering / refreshing / deleting a note across **both** the search index and this mapping in one go, use `index-add` / `index-update` / `index-delete` — they call `sync`/`remove` for you.

## Path & term rules

- **Note path** must be under `terminologies/notes/` (a bare filename like `260604_vllm.md` is accepted and expanded).
- **Terminology lookups are exact-string**, not fuzzy — `notes "KV cache (Key–Value cache)"` must match the term verbatim (including the en-dash and parentheses). If the user only knows a partial name, run `mapping.py list` to find the exact string, or `index-search` to find the note.
- For `sync` to register terms, the note's `### Key terminologies` bullets must be in `- **Term** — definition` form (the parser takes the first bold span of each bullet).

## Run

```
python3 terminologies/index/mapping.py terminologies terminologies/notes/<file>.md
python3 terminologies/index/mapping.py notes "<terminology>"
python3 terminologies/index/mapping.py list
python3 terminologies/index/mapping.py sync terminologies/notes/<file>.md
python3 terminologies/index/mapping.py remove terminologies/notes/<file>.md
```

Errors:

- `note path missing prefix: …` — path isn't under `terminologies/notes/`.
- `file not found: …` (on `sync`) — note isn't on disk.
- `not in mapping: …` (on `remove`) — already gone or typo. Surface; don't retry.
- `(no matches)` (on a lookup) — print plainly. Likely a typo, an unsynced note, or a term that no note defines yet.

## Report

- **terminologies <note>** — single sentence framing (*"Terminologies defined in `<note>`:"*) + bulleted list, in the note's own order.
- **notes <terminology>** — single sentence framing (*"Notes that define `<terminology>`:"*) + bulleted list. If more than one note defines it, that's a useful cross-link, not a duplicate-to-fix.
- **list** — print the master list; mention the count.
- **sync / remove / rebuild** — one line confirming the change and the new terminology count; note that `index.md` was regenerated.

## Refusals

- One note per `sync` / `remove` call (no bulk syntax). Cluster multiple confirmations into one summary.
- Don't run `rebuild` for a single-note change — that re-parses every note; only on explicit request.
- Don't fall back to BM25 search inside this skill — point at `index-search` for partial-name / body lookups.
- Don't hand-edit `notes_terminologies_mapping.json` or `index.md` — always go through the script.
