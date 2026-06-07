---
name: terminology-create
description: Explain a technical terminology, or the relevancy/relationship between two or more terminologies, for a computer-science bachelor student, and save it as a terminology note. Searches the internet for up-to-date context, then produces an itemized explanation with concrete examples and an explicit "how they connect" section. Use when the user asks "what is X", "explain X", "X vs Y", "how does X relate to Y", or "difference between X and Y".
argument-hint: "[term, or 'X vs Y', or 'how does X relate to Y']"
allowed-tools: WebSearch, WebFetch, Read, Write, Bash
---

# Explain Terminology

Given a user query about a single terminology **or** the relationship between multiple terminologies, search the internet for current context and produce a clear, itemized explanation tailored to a **computer-science bachelor student**.

## Input

The user query is: $ARGUMENTS

Parse the query into one of two modes:

- **Single-term mode** — one terminology to explain (e.g. "what is a vector database", "explain eBPF").
- **Relationship mode** — two or more terminologies whose relevancy/relationship is asked (e.g. "REST vs GraphQL", "how does CUDA relate to cuDNN", "difference between TCP and UDP").

If the query is empty or ambiguous about which term(s) are meant, ask the user to name the terminology (or terminologies) before proceeding.

## Audience Assumptions

The reader is a **CS bachelor student**:
- Comfortable with: data structures, basic algorithms, OOP, a general-purpose language, intro OS/networking/databases, Big-O.
- Likely shaky on: industry-specific jargon, very recent tools/standards, deep systems internals, niche math.

So: **anchor new terms to undergraduate-level concepts they already know**, define jargon the first time it appears, and prefer concrete code/system examples over abstract prose. Do not dumb it down — keep it technically correct and precise.

---

## Execution Flow

### Phase 1: Get up-to-date context (internet search)

Terminology drifts and new tools appear constantly, so **always search** rather than relying on memory alone.

1. Run **WebSearch** for each term. Use focused queries, e.g. `"<term> meaning"`, `"<term> explained"`, and for relationship mode also `"<term A> vs <term B>"` and `"<term A> <term B> relationship"`.
2. Skim the results for the **2–4 most authoritative sources** (official docs, standards bodies, reputable engineering blogs, well-known references). Prefer primary sources over content farms.
3. Use **WebFetch** on those sources to pull precise, current definitions and details. Note any recent changes, version differences, or shifts in common usage.
4. If sources disagree or a term is overloaded (means different things in different contexts), capture each distinct meaning — you will disambiguate in the output.

Keep track of which source backs which claim so you can cite them at the end.

### Phase 2: Synthesize the explanation

Structure the answer using the template below. Fill **every** section. Concrete examples are mandatory, not optional.

**Canonical example to match:** read `terminologies/notes/260604_vllm.md` — it is the reference for the expected output quality and shape (a decomposed **Key terminologies** list, a numbered **How these terms are related** causal chain ending in a one-line `A → B → ... → Term` summary, a concrete runnable example, and cited sources). Aim for that style and depth.

### Phase 3: Write the output

Always **save** the explanation as a markdown file, then also show it inline in the conversation.

**Output path:** `terminologies/notes/{yymmdd}_{filename}.md`

- `{yymmdd}` — today's date, zero-padded (e.g. `260604`).
- `{filename}` — a short, underscore-lowercased name derived from the term(s) (≤ 50 chars). For relationship mode join the terms, e.g. `rest_vs_graphql`, `cuda_vs_cudnn`; for single-term mode just the term, e.g. `vector_database`, `ebpf`.
- Create the `terminologies/notes/` directory first if it does not exist (`mkdir -p terminologies/notes` — note: this requires Bash; if Bash is unavailable, Write will create parent dirs).

After writing, tell the user the saved path.

### Phase 4: Update the index

So the note is searchable and its terminologies are registered, run both indexers on the file you just wrote (stdlib-only Python, no deps) — this is exactly what the **`index-add`** skill does:

```bash
python3 terminologies/index/bm25.py add terminologies/notes/{yymmdd}_{filename}.md
python3 terminologies/index/mapping.py sync terminologies/notes/{yymmdd}_{filename}.md
```

- `bm25.py add` adds the note to the full-text BM25 index (`notes.json`). If you overwrote an existing note, use the **`index-update`** skill (`bm25.py edit`) instead.
- `mapping.py sync` parses the note's **Key terminologies** section, updates `notes_terminologies_mapping.json`, and regenerates the master list at `terminologies/index/index.md`.

- For a **duplicate-aware** merge into the glossary, use the **`terminology-indexing`** skill instead of `index-add` — it BM25-checks each of the note's terms against the existing terminologies (`terminologies.json`) and reconciles near-duplicates to the existing canonical term before generating glossary pages. Prefer it once the glossary has grown enough that the same concept might already exist under a different name.

For the mapping to pick up the terms, the **Key terminologies** bullets MUST use the `- **Term name** — definition` form (bold term first) — the parser keys on the first bold span of each bullet.

**Before** writing a new note, dedupe and find terms to cross-link with the **`index-search`** skill (BM25 over note bodies) or **`index-mapping`** (`list` / `notes "<term>"` for exact-term lookups). The companion skills — `index-add`, `index-update`, `index-delete`, `index-search`, `index-mapping`, `terminology-indexing` — manage this index end to end.

---

## Output Template

### Single-term mode

Do not write a one-paragraph encyclopedia entry. **Decompose the main term into the
web of smaller terminologies you need in order to understand it**, define each one,
then show how they chain together. The decomposition + the chain are the whole point.

```markdown
## {Term}

**In one sentence:** {plain-language definition a CS student gets immediately, naming
the main term and the one idea that makes it tick.}

### Key terminologies
{List EVERY sub-term a student must know to understand {Term} — usually 6–10 of them.
Order them so each builds on the previous (foundational concepts first, the main term
last). Each is one bolded name + a 1–2 sentence plain definition. Anchor to undergrad
knowledge and define jargon inline.}

- **{sub-term 1}** — {definition.}
- **{sub-term 2}** — {definition.}
- **{sub-term 3}** — {definition.}
- ... (continue through all the relevant sub-terms)
- **{Term}** — {the main term, defined last, now that its parts are on the table.}

### How these terms are related
{The heart of the answer. Walk the terms as a CAUSAL CHAIN — a numbered list where
each step introduces the next term and explains why it follows from the previous one
("because X, we need Y; but Y causes Z; to fix Z we use W"). This is what turns a
glossary into understanding.}

1. **{step naming term A → term B}** — {why B follows from A.}
2. **{step naming term B → term C}** — {...}
3. ... (continue until you reach {Term})

**The chain in one line:**
`{Term A} → {Term B} → {Term C} → ... → {Term}` {with a 2–4 word gloss on each arrow.}

### Concrete example
{A specific, real scenario — ideally a tiny code snippet, command, or walked-through
system flow — where you can point at the sub-terms doing their jobs. Make it tangible,
not "imagine a system that...".}

### Where you'll meet it
{Real tools/standards/companies/courses where this shows up, so the term is grounded.}

### Common confusions
{1–3 things students mix this up with, and the one-line distinction for each.}

---
**Sources:** {linked authoritative sources used.}
```

### Relationship mode

```markdown
## {Term A} vs / and {Term B} {(+ Term C ...)}

**TL;DR:** {one sentence stating the core relationship — same layer? competitors?
one builds on the other? complementary?}

### The terminologies, itemized
- **{Term A}** — {concise definition, anchored to a known concept.}
- **{Term B}** — {concise definition.}
- **{Term C}** — {if present.}

### How they connect
{The heart of the answer. Explain the actual relationship explicitly: is one a
specialization of the other, do they sit at different layers of a stack, do they
compete to solve the same problem, does one use the other as a dependency, etc.
A small ASCII diagram is encouraged when it clarifies the relationship — e.g. a
layered stack, a "competes-with" pair, or an "A → uses → B" arrow.}

### Side-by-side comparison
| Aspect            | {Term A}        | {Term B}        |
| ----------------- | --------------- | --------------- |
| What it is        | ...             | ...             |
| Problem it solves | ...             | ...             |
| When to use it    | ...             | ...             |
| Trade-offs        | ...             | ...             |

### Concrete example
{One scenario where BOTH terms appear together, showing how they interact —
ideally a code snippet or a system flow where you can point at each term doing
its job. If they are pure alternatives, show the SAME task done each way.}

### Rule of thumb
{A memorable one-liner the student can use to pick between / remember them.}

---
**Sources:** {linked authoritative sources used.}
```

---

## Rules

1. **Always search first.** Never explain from memory alone — terminology and tooling change. At minimum one WebSearch per term, plus WebFetch on the best source(s).
2. **Cite sources.** End with the authoritative links you actually used. Don't fabricate URLs.
3. **Concrete examples are mandatory.** Every explanation includes at least one specific, tangible example (code, command, or a walked-through flow). "Imagine a system…" hand-waving is not an example.
4. **Anchor to undergrad knowledge.** Connect new terms to things a CS bachelor student already learned (a course, a data structure, a protocol they've seen).
5. **Define jargon on first use.** If explaining term X requires term Y the student likely doesn't know, give Y a one-line gloss inline.
6. **Always answer "how do they connect," in both modes.** Single-term mode decomposes the term into its sub-terminologies and chains them (ending in a one-line `A → B → ... → Term` summary); relationship mode explains the relationship between the given terms. Never just define terms in isolation and stop — the connection is the point.
7. **Disambiguate overloaded terms.** If a term means different things in different contexts (e.g. "kernel" in OS vs ML), say so and cover the meaning the user most likely intends, briefly noting the other.
8. **Stay precise.** Simplify the framing, not the facts. No incorrect analogies for the sake of being approachable.
9. **Always save the file** to `terminologies/notes/{yymmdd}_{filename}.md` and report the path, in addition to showing the explanation inline.
10. **Always update the index (Phase 4)** after saving — run `bm25.py add/edit` and `mapping.py sync` on the new note so it's searchable and its terminologies are registered. Keep the **Key terminologies** bullets in `- **Term** — def` form so the mapping parser can read them.
