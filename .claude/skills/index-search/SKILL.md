---
name: index-search
description: Full-text BM25 search over the terminology notes (terminologies/notes/*.md) for the notes most relevant to a free-text query. Wraps `python3 terminologies/index/bm25.py search "<query>" --top-k N`. Returns top hits as note paths with BM25 scores; quotes a salient passage of the top hit so the user can confirm relevance without opening the file. Use when the user wants to find a terminology note by topic — phrases like "search terminologies for X", "which note covers KV cache", "find the note about paging", "do we already have a note on X".
effort: low
---

# Index Search

BM25 full-text search over the terminology notes corpus.

## When to use

- Finding a note by topic or keyword ("which note explains continuous batching?").
- Checking whether a terminology is already covered before writing a new note (dedupe).
- Surfacing related notes to cross-link from a new explanation.

If the user already names the exact file (e.g. "show me terminologies/notes/260604_vllm.md"), do **not** use this skill — just `Read` the file.

For looking up which note *defines* an exact terminology, or listing the terms in a note, use `index-mapping` (exact-match), not this BM25 skill.

## Run

```
python3 terminologies/index/bm25.py search "<query>" --top-k 5
```

- Pass the query verbatim, trimmed to content words (drop "find me a note about…").
- Default `--top-k` is 5. Bump to 10 on "all" / "more"; drop to 3 for a focused look.
- Output is one line per hit: `<path>  <score>`. Zero matches prints `(no matches)`.
- Search is **local-only** (this project's notes). Don't run `rebuild` unless the user explicitly asks — assume the index is current.

## Report

1. **List** the top hits as a numbered Markdown list (filename + score).
2. **Read** the top hit and quote a salient passage so the user can confirm at a glance — prefer the **In one sentence** line and the relevant `### Key terminologies` bullet(s).
3. **Offer to dive deeper** — open the full note, or run `index-mapping` to see every terminology that note defines.

On `(no matches)`: say so plainly, suggest a broader query, and note that the topic may not have a note yet (offer `terminology-create` to create one). Don't fabricate hits.

## Refusals

- Don't fall back to grep / file listing if BM25 errors — surface the error.
- Don't invent scores; quote the script's numbers.
- Don't search anything outside `terminologies/notes/` — this corpus is notes only.
