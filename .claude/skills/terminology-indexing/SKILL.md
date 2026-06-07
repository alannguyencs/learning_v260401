---
name: terminology-indexing
description: Index a terminology note's terms into the glossary with BM25 duplicate detection and definition merging. Extracts the terms from a note's `### Key terminologies` section, compares each against existing terminologies (terminologies/index/terminologies.json, a BM25 index over the glossary), reconciles near-duplicate names to a canonical term, and for terms already in the glossary MERGES the existing and new definitions into one combined entry (instead of competing bullets or overwriting) — especially for general concepts like dot product or softmax that many notes define from their own angle. Then regenerates the glossary pages and updates terminologies/index/notes_terminologies_mapping.json. Use after a note is written/edited when you want its terminologies merged into the glossary without duplicates — phrases like "index the terminologies in X", "merge X's terms into the glossary", "dedupe and index this note's terms".
argument-hint: "[terminologies/notes/{yymmdd}_{slug}.md]"
allowed-tools: Bash, Read, Edit, Grep
---

# Terminology Indexing

Merge a note's terminologies into the shared glossary **without duplicates**. Unlike `index-add` (which blindly syncs every term the note names), this skill first checks each term against the existing terminology set with BM25, so a concept already in the glossary under a slightly different name is reused instead of duplicated.

## Input

The note path is: $ARGUMENTS — a file under `terminologies/notes/` (e.g. `terminologies/notes/260604_vllm.md`). If empty, ask which note to index. If only a slug/filename is given, expand to the full path.

## The two indexes involved

- **`terminologies/index/terminologies.json`** — a BM25 index whose *documents are the glossary pages* (`terminologies/glossary/*.md`), i.e. one document per existing terminology (title + definition). This is the dedup backbone. Build/refresh it with `bm25.py rebuild --corpus terminologies`.
- **`terminologies/index/notes_terminologies_mapping.json`** — the note → terminologies map. `mapping.py sync` derives it from the note's `### Key terminologies` bullets and regenerates the glossary pages + `index.md`.

---

## Execution Flow

### Phase 1: Refresh the terminology index

Make sure the dedup index reflects the current glossary before searching:

```bash
python3 terminologies/index/bm25.py rebuild --corpus terminologies
```

(If `terminologies.json` doesn't exist yet, this creates it. An empty glossary just yields an empty index — then nothing is a duplicate and every term is new.)

### Phase 2: Extract the note's terminologies

List the term names, and Read the note to get each term's definition (the text after `—` on its `- **Term** — definition` bullet in the `### Key terminologies` section):

```bash
python3 terminologies/index/mapping.py terminologies terminologies/notes/<file>.md
```

If the note has no `### Key terminologies` section (0 terms), stop and tell the user — there's nothing to index (offer `terminology-create` to author one).

### Phase 3: Dedup-check each term

For **each** extracted term, search the terminologies corpus with the term name plus a few words of its definition:

```bash
python3 terminologies/index/bm25.py search "<term name>. <short definition>" --corpus terminologies --top-k 3
```

Then judge each result — **BM25 surfaces candidates; you decide**, sorting each of the note's terms into one of three buckets:

- **Ignore self-matches.** On a re-run the term may already have its own glossary page (`<slug>.md`); a hit whose title equals the term is the term itself.
- **Confirm by reading the candidate.** Open the top glossary hit (`terminologies/glossary/<slug>.md`) and compare concepts, not just word overlap. A high score on shared generic words (e.g. "memory", "model") is **not** the same concept.
- **New** = no candidate is the same concept. Leave the term as written → Phase 6 creates its glossary page.
- **Duplicate name** = the candidate describes the *same concept under a different name* (synonym/abbreviation/super- or sub-set — e.g. "KV-cache" vs "KV cache (Key–Value cache)"). Canonicalize the name in **Phase 4**.
- **Shared term** = the candidate is the *same concept with the same (or now-canonical) name*, but the note's definition differs from the glossary's. Especially common for **general concepts** (e.g. *Dot product*, *Softmax*, *Vector*) that many notes legitimately define from their own angle. Merge the definitions in **Phase 5** — do **not** leave two competing bullets, and do **not** silently overwrite one with the other.

When unsure whether two things are the same concept, prefer **new** and flag it — collapsing two distinct concepts is worse than a near-duplicate.

### Phase 4: Reconcile duplicate names

For each **duplicate name**, rewrite **only the bold term** in the note's `### Key terminologies` bullet to the canonical title, with `Edit` — leave its definition text alone for now (Phase 5 handles definitions):

```
- **KV-cache** — …        ->   - **KV cache (Key–Value cache)** — …
```

This makes `mapping.py sync` map the note onto the existing canonical terminology instead of creating a second page. If there were no duplicate names, skip this phase.

### Phase 5: Merge definitions for shared terms

A glossary page is generated mechanically from the `- **Term** — definition` bullets of **every** note that defines the term, and identical definition strings collapse to one. So to get a **single merged definition** (rather than two competing bullets, or one clobbering the other), synthesize the merge and write the *same* text into every defining note's bullet.

For each **shared term** (and each term you just canonicalized in Phase 4):

1. **Gather the definitions.** Find every note that defines the term and read its bullet:
   ```bash
   python3 terminologies/index/mapping.py notes "<canonical term>"
   ```
   Collect the existing glossary/notes definition(s) **and** the new note's definition.
2. **Synthesize one merged definition.** Integrate — don't concatenate: keep each distinct, correct point; drop redundancy; for a general concept, lead with the context-agnostic meaning, then fold in the salient context-specific nuances. Stay concise and precise.
3. **Propagate it.** With `Edit`, write that **byte-identical** merged definition into the `- **Term** — …` bullet of **every** note that defines the term (the new note *and* each pre-existing one). Identical text is what makes the glossary render a single merged entry.

If a "shared term" turns out to describe a genuinely different concept on closer reading, treat it as **new** instead (back to Phase 3) — don't force-merge unrelated ideas.

### Phase 6: Sync the mapping + regenerate the glossary

Sync **every** note you touched (the new note, plus any pre-existing notes whose bullets you edited in Phase 5):

```bash
python3 terminologies/index/mapping.py sync terminologies/notes/<file>.md
```

This updates `notes_terminologies_mapping.json`, regenerates each affected glossary page (now a single merged definition per shared term), and rebuilds `index.md`.

### Phase 7: Refresh both indexes

Re-index the terminologies corpus so the merged/new terms are searchable next run, and refresh the notes corpus for `index-search`:

```bash
python3 terminologies/index/bm25.py rebuild --corpus terminologies
python3 terminologies/index/bm25.py add  terminologies/notes/<new-note>.md     # the new note
python3 terminologies/index/bm25.py edit terminologies/notes/<other-note>.md   # any note edited in Phase 5
```

### Phase 8: Report

Summarize:
- **New terminologies** added (with their glossary filenames).
- **Duplicate names reconciled** — each as `note's term → canonical term`.
- **Definitions merged** — each shared term, listing which notes' definitions were combined, so the user can review the synthesis.
- Confirm `notes_terminologies_mapping.json`, the glossary, and both BM25 indexes are updated.

---

## Rules

1. **Always refresh `terminologies.json` before searching** (Phase 1) and again after syncing (Phase 7) — a stale dedup index produces wrong duplicate decisions.
2. **BM25 ranks; you judge.** Never act on score alone — read the candidate glossary page and confirm whether it's the same concept before renaming or merging. Generic-word overlap is not the same concept.
3. **Two kinds of edit, both to the Key-terminologies bullet:** reconcile a duplicate *name* by editing the bold term (Phase 4); merge a *definition* by replacing the bullet's definition text with the synthesized merge (Phase 5). Never touch the note's other prose.
4. **Merge, don't pick or duplicate.** When a term is defined by more than one note, the glossary entry must be a single *synthesis* of all their definitions — never two competing bullets, and never one definition silently clobbering another. Propagate the byte-identical merged text to every defining note so the mechanical glossary collapses it to one entry.
5. **General concepts get merged, not pinned.** Terms like *dot product*, *softmax*, *vector* recur across notes with context-specific framings; combine them into one context-aware definition rather than freezing the first note's wording.
6. **When uncertain whether two things are the same concept, keep the term as new and flag it.** Collapsing two distinct concepts is worse than a near-duplicate.
7. **Report every reconciliation and merge** (`term → canonical`; `merged definitions of X from notes A + B`) so the user can review and object.
8. **Don't hand-edit** `terminologies.json`, `notes_terminologies_mapping.json`, `index.md`, or the glossary pages — drive them through `bm25.py` / `mapping.py`; edit only the source notes' bullets.
9. Relationship to siblings: `terminology-create` writes the note; **this skill** is the careful indexer (dedup + merge); `index-add` is the quick indexer (no dedup); `index-mapping` / `index-search` query the results.
