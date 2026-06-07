---
name: lesson-create
description: Transform a raw markdown doc (in data/raw/{topic}/{yymmdd}.md) into a lesson file under data/lesson/{topic}/ — one lesson section per raw `##` section, each with rich prose, bolded key points, and an ASCII diagram. Use when the user points at a raw .md file and asks to turn it into a lesson.
argument-hint: "[path/to/raw.md]"
allowed-tools: Bash, Read, Write, Glob
---

# Raw Markdown to Lesson

Given a raw markdown file (a collection of short `##` sections), produce a lesson file that mirrors the raw structure 1:1 — **same number of sections, same order, same topics** — but each section expanded into a teaching-grade passage with an ASCII diagram.

## Input

The user argument is: $ARGUMENTS

Parse it as the path to a raw markdown file, e.g. `data/raw/anthropic/260421.md`.

## Naming Convention

- **Topic folder** = parent directory of the raw file (`data/raw/anthropic/260421.md` → `anthropic`).
- **Date stem** = basename of the raw file without extension (`260421`).
- **Slug** = short, underscore-lowercased phrase that captures the lesson's overall theme (≤ 50 chars). Derive it from the H1 title you write, not from the raw filename.
- **Output path**: `data/lesson/{topic}/{yymmdd}_{slug}.md`

Example: `data/raw/anthropic/260421.md` → `data/lesson/anthropic/260421_claude_101.md`

---

## Execution Flow

### Phase 1: Read the raw doc

Use **Read** on the raw file. Count the `##` headings — **this is the target section count for the lesson.** Do not merge, split, drop, or reorder sections.

### Phase 2: Read a style reference

Read **`data/lesson/coach/260324_time_framed_learning.md`** as the canonical style reference. Note:
- H1 title at the top synthesizing the whole lesson.
- `---` separator between sections.
- Each `##` section has: 1–3 paragraphs of rich prose + a fenced ASCII diagram.
- Bold the key terms and phrases inline (not just in bullet lists).
- Bullet lists are fine for enumerations (like the 4 Ds), but the diagram is required regardless.

### Phase 3: Draft the lesson

For each raw `##` section, write a matching lesson section:

1. Keep the **same heading** (lightly reworded if needed for clarity, but same concept).
2. Open with a **definitional sentence** that bolds the core term.
3. Expand the raw section's key points into **1–3 paragraphs** of connected prose. Use bold for the concepts a learner must remember.
4. If the raw section enumerates items (e.g. Delegation / Description / …), render them as a bulleted list with the item name bolded.
5. End the section with a **fenced ASCII diagram** that illustrates the concept — a flow, a comparison, a layered structure, a lifecycle, etc. Keep it within ~65 columns wide.
6. Separate sections with `---` on its own line (blank line above and below).

H1 title: write a single **synthesizing H1** at the top that names the through-line across all sections (e.g. "Claude 101: AI Fluency, CLAUDE.md, and the Extensibility Surface of Claude Code"). Do not just concatenate section titles.

### Phase 4: Write the file

Ensure the output directory exists, then use **Write** to create the lesson markdown:

```bash
mkdir -p data/lesson/{topic}
```

### Phase 5: Display summary

After writing, print:

```
Lesson saved: data/lesson/{topic}/{yymmdd}_{slug}.md

Sections ({N}):
  1. {section 1 heading}
  2. {section 2 heading}
  ...
```

---

## ASCII Diagram Guidelines

Pick the diagram type that fits the section's shape — do not reuse the same layout for every section.

| Section shape                     | Diagram type                                  |
| --------------------------------- | --------------------------------------------- |
| A loop / cycle                    | Boxes joined by `│ ▼` arrows, final feedback arrow back to start |
| An ordered procedure              | Numbered steps stacked vertically with `▼` transitions |
| A comparison / trade-off          | Two side-by-side columns, or stacked bar chart |
| A layered system / context budget | Stacked horizontal bars with labels and percentages |
| A lifecycle with event hooks      | Timeline with labeled hook points             |

Every diagram should be wrapped in a fenced code block (no language tag) and bordered with a `─`-rule line at the top and bottom. End with a one-line takeaway when helpful.

---

## Rules

1. **Section count is sacred** — N `##` in the raw file ⇒ exactly N `##` in the lesson.
2. **Do not invent facts** not present in the raw file. You may add framing, structure, and synthesis, but the technical claims must trace back to the raw source.
3. **Every section gets an ASCII diagram.** No exceptions.
4. **Vary diagram types** across sections — a lesson where all diagrams are boxes-and-arrows is a failure of craft.
5. **Bold the key terms** inline in prose. A learner skimming should catch the concepts without reading every word.
6. **One H1 at the top**, synthesizing. Never multiple H1s.
7. **Use `---` between sections**, matching the style reference.
8. Do not add a citations/references section if the raw file has none.
9. If the raw file has fewer than 2 sections, tell the user the doc is too thin and ask whether to proceed or wait for more content.
