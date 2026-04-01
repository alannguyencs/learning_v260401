---
name: lesson-quiz-generate
description: Generate Quiz Questions from Lesson File
---

# Generate Quiz Questions from Lesson File

Read a lesson file and generate a set of quiz questions **per section**, then save them as a JSON file in `data/quiz/`.

**Argument:** `<path to lesson markdown file>`

Example: `data/lesson/themitmonk/250218_20_quantum_cheat_codes.md`

---

## Quiz Set Per Section

For each lesson section (skipping **Section 0** — it is reference material only), generate exactly **9 quizzes**:

| Format | Count | File |
|--------|-------|------|
| Free recall | 1 | `free_recall.md` |
| Teach-back | 1 | `teach_back.md` |
| Cloze deletion | 2 | `cloze_deletion.md` |
| Multiple choice | 5 | `multiple_choice.md` |

A lesson with 5 sections (1–5) produces **45 quiz questions** total.

---

## Instructions

1. Parse `$ARGUMENTS` to extract the **lesson file path**.
2. Read the following files **in parallel**:
   - The lesson file at the extracted path
   - The metadata file at `data/metadata/{lesson_base_name}.json`
   - The user's background at `.claude/skills/personal_background.md`
   - All 4 quiz type guides:
     - `.claude/skills/lesson-quiz-generate/references/free_recall.md`
     - `.claude/skills/lesson-quiz-generate/references/teach_back.md`
     - `.claude/skills/lesson-quiz-generate/references/cloze_deletion.md`
     - `.claude/skills/lesson-quiz-generate/references/multiple_choice.md`
3. Identify all sections in the lesson file. Sections are marked with `## Section N:` headers. **Skip Section 0** (Material).
4. For each section (in order), generate the 9 quizzes following the rules in each type's `.md` file:
   - Use the user's background (R&D startup, Hong Kong, family budgeting, PhD in AI/ML) to personalise **application** scenarios in multiple choice and **teach-back** prompts where relevant.
   - Each quiz must include `"section"` (the section number as a string, e.g. `"1"`) and `"section_name"` (the section's heading, e.g. `"Summary"`).
   - Ensure the 2 cloze deletions per section target **different concepts**.
   - Ensure the 5 multiple choice questions span at least 3 different cognitive levels (recall, understanding, application, analysis).
5. Collect all questions into a single flat JSON array (all sections combined, ordered section by section).
6. Save to `data/quiz/{lesson_filename}.json`. Create `data/quiz/` if it does not exist.

---

## Unified Quiz Fields

Every quiz object — regardless of format — must include:

| Field | Type | Description |
|-------|------|-------------|
| `lesson_title` | str | Title from the metadata JSON |
| `section` | str | Section number as string, e.g. `"1"` |
| `section_name` | str | Section heading, e.g. `"Summary"` |
| `quiz_format` | str | One of: `free_recall`, `teach_back`, `cloze_deletion`, `multiple_choice` |

Additional fields per format are defined in the respective `.md` files.

---

## Save to JSON

Write all questions as a JSON array to `data/quiz/{lesson_filename}.json` (strip `.md` from the lesson filename). Use the **Write tool** to create the file.

---

## Output

After saving, print the file path and a summary table:

| Section | free_recall | teach_back | cloze_deletion | multiple_choice | Total |
|---------|-------------|------------|----------------|-----------------|-------|
| 1 — Summary | ✓ | ✓ | 2 | 5 | 9 |
| 2 — Recommendation | ✓ | ✓ | 2 | 5 | 9 |
| ... | | | | | |
| **Total** | | | | | **N** |

---

## Rules

- **Skip Section 0** — it is metadata/reference, not learnable content
- Do NOT generate duplicate or near-duplicate questions within the same section
- Every explanation in multiple choice must say WHY an option is correct or incorrect
- Every question must be self-contained — embed necessary context in the question stem
- Use the personal background to make application questions feel concrete and relevant
- Verify the lesson file exists before proceeding
