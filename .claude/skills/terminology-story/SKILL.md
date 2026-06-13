---
name: terminology-story
description: Transform a terminology note (terminologies/notes/{yymmdd}_{slug}.md) into a spoken-style verbal lesson and save it to terminologies/stories/. Rewrites the itemized note as one continuous lecture an expert gives out loud to junior students — no section titles, no bullet lists, just coherent flowing prose with bold for emphasis and a few simple ASCII diagrams. Use when the user says "make a story from X", "turn this note into a verbal lesson", "story-ify terminologies/notes/X.md", or "transform X into a spoken lesson".
argument-hint: "[path to a terminologies/notes/*.md file]"
allowed-tools: Read, Write, Bash
---

# Terminology → Story

Given a terminology **note** at `terminologies/notes/{yymmdd}_{slug}.md`, transform it into a **verbal lesson**: a single continuous lecture, as if an **expert in the domain were teaching it out loud to a group of junior-level students**. Save the result to `terminologies/stories/{same-filename}.md`.

The note is the *itemized reference* (definitions, charts, bullets). The story is the *spoken retelling* of that same material — same concepts, same examples, same characters, but reshaped into coherent prose that flows from one idea to the next.

## Input

The target note is: $ARGUMENTS

This should be a path to a file under `terminologies/notes/`. If the argument is empty, ask the user which note to transform. If it names a term rather than a path, find the matching note (e.g. with the **`index-search`** skill or by listing `terminologies/notes/`) and confirm before proceeding.

## Execution Flow

### Phase 1: Read and understand the note

1. **Read** the target note in full.
2. Identify its backbone:
   - the **ordered chain of concepts** (in a well-formed note these build on each other top-to-bottom and culminate in the main term);
   - the **recurring characters/objects** used in examples (e.g. Alan, Chloe, a post, a salary row) — reuse these exact ones;
   - the **concrete example / walked-through scenario** — keep it, retold conversationally;
   - the **common confusions** and **where you'll meet it** — fold these into the closing of the lecture.

The note's structure IS the lecture's structure. Do not reorder the concepts; the whole value of the note is that each concept's weakness motivates the next one.

### Phase 2: Write the verbal lesson

Write one flowing lecture. The hard constraints (what makes it a *verbal* lesson and not a copy of the note):

- **No section titles / headings** anywhere except the single top-level `# {Term}` title at the very top.
- **No bullet lists, no numbered lists, no tables.** Every itemized point from the note becomes a sentence or clause inside a paragraph.
- **Bold is allowed** — and encouraged — but only to *emphasize* key terms and turning points, the way a speaker leans on a word. Do not bold whole sentences.
- **Coherent connective tissue is the point.** Each concept must hand off to the next with an explicit causal/spoken transition ("but here's where that runs out of room…", "and once you say the word *path*, you've basically invented the next idea…"). One concept's limitation is the next concept's reason to exist. Never just define a term and stop.
- **Spoken voice.** Address the students directly ("notice straight away…", "slow down here…", "let me leave you with…"). It should read like a transcript of a good lecturer, not an essay.
- **Repeat the key term instead of pronouns.** In the paragraph that introduces or explains a key term, name the term again rather than referring back to it with "it / this / they". Where you'd normally write "It knows nothing about MCP. It just answers requests," write "The **API server** knows nothing about MCP. The **API server** just answers requests." The deliberate repetition drills the term in — that's the point of a spoken lesson. (One memorable aphorism per paragraph may keep a pronoun, e.g. "the model proposes, something else disposes.")
- Preserve the **recurring cast** and the **concrete example** from the note, retold in narration rather than as a code walkthrough.

### Phase 3: Add simple ASCII diagrams

Sprinkle a **few** small ASCII diagrams through the lecture — placed right **after** the paragraph each one illustrates. Rules for these diagrams:

- **Simple.** Just a little terminology connected by arrows / `OR` / short labels. A few lines at most.
- They illustrate the point of the *paragraph they follow* — one diagram per key idea, not a master chart of the whole topic.
- Do **not** copy the big composite chart from the note's `### Key terminologies` block. Break the idea into small per-paragraph snapshots instead.
- Each in a fenced ```code block```.
- Aim for roughly one diagram per major concept (typically 6–9 across the lesson). Don't overdo it — the prose carries the lesson; the diagrams are punctuation.

Examples of the right altitude (simple, terminology connected):

```
subject ──action──> resource  ?  →  allow / deny
```

```
RBAC   →  what role do you have?
ABAC   →  do your details match the resource's?
ReBAC  →  is there a path from you to the resource?
```

### Phase 4: Save the story

**Output path:** `terminologies/stories/{filename}.md` — the **same filename** as the source note (same `{yymmdd}_{slug}.md`), only the directory changes from `notes/` to `stories/`.

- Create the directory first if needed: `mkdir -p terminologies/stories`.
- The file starts with `# {Term}` (a clean title — just the term, no "told out loud" or other decoration) and then the lecture.
- After writing, tell the user the saved path.

There is **no index step** for stories — the BM25 index and the note↔terminology mapping cover `terminologies/notes/` only. Do not run `bm25.py` or `mapping.py` on a story file.

## Rules

1. **One continuous lecture.** No headings (except the top `# {Term}`), no bullets, no numbered lists, no tables. Every itemized point becomes prose.
2. **Bold for emphasis only.** Lean on key terms and pivots; never bold whole sentences.
3. **Preserve the concept order of the note.** The note is built so each idea motivates the next — keep that spine. The lecture's coherence comes from explicit hand-off transitions between concepts.
4. **Reuse the note's recurring cast and concrete example.** Same characters (Alan, Chloe, …), same walked-through scenario, retold conversationally.
5. **A few simple ASCII diagrams, placed after the paragraph they illustrate.** Just terminology connected by arrows/`OR` — not the note's big composite chart. ~6–9 across the lesson.
6. **Spoken voice throughout.** Address the students directly; it should read like a transcript of an expert teaching juniors, not a written article.
7. **Repeat the key term, don't pronoun it.** Within a term's introductory/explanatory paragraph, restate the actual term (the **API server**, the **LLM**, the **MCP Client**, the **tool**…) in place of "it / this / they". The repetition is intentional reinforcement; reserve a pronoun only for the occasional aphorism.
8. **Same filename, stories/ directory.** `terminologies/notes/X.md` → `terminologies/stories/X.md`. Report the path. No index step.
9. **Stay technically correct.** Simplify the framing and the delivery, not the facts.
