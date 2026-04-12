---
name: en-lesson-quiz-generate
description: Generate quiz questions from an English vocabulary lesson file. Use when the user wants to generate quizzes from a vocab lesson in data/lesson/.
argument-hint: "[path to vocab lesson .md file]"
---

# Generate Quiz Questions from English Vocabulary Lesson

Read a vocabulary lesson file and generate quiz questions based on the vocabulary words, then save them as a JSON file in `data/quiz/`.

**Argument:** `<path to vocab lesson markdown file>`

Example: `data/lesson/learning_phrases_with_chris_friends/211118_useful_english_cartoons_my_room_basic_english_vocab.md`

---

## Quiz Types

Only two quiz formats are used:

| Format | File |
|--------|------|
| Cloze deletion | `references/cloze_deletion.md` |
| Multiple choice | `references/multiple_choice.md` |

---

## Quiz Count — 2x Vocabulary, One Set Per Chapter

The lesson has multiple chapters (sections after Material). Generate **one set of N quizzes per chapter**, where N is the number of vocabulary words.

**Formula:**
- Count the total vocabulary words/phrases (N) from the Vocabulary section tables
- Count the chapters in the lesson (sections after Material, e.g. Vocabulary, Story = 2 chapters)
- Generate **N quizzes per chapter** → total = **N x number_of_chapters**
- Each set: split roughly **40% cloze deletion, 60% multiple choice** (round as needed)

**Example:** 21 vocabulary words, 2 chapters (Vocabulary + Story) → 21 + 21 = 42 quizzes total

### Per-chapter quiz design

Each chapter's quiz set tests the **same vocabulary words** but from a **different angle**:

- **Chapter 1 (Vocabulary)**: quizzes focus on **definition recall** — can the user remember what the word means? Use transcript sentences and definition-based questions.
- **Chapter 2 (Story)**: quizzes focus on **contextual usage** — can the user use the word in a new situation? Use story-derived sentences and application scenarios.

The two sets must NOT duplicate questions. Each vocabulary word appears once per chapter, tested differently.

---

## Instructions

1. Parse `$ARGUMENTS` to extract the **lesson file path**.
2. Read the following files **in parallel**:
   - The lesson file at the extracted path
   - The user's background at `.claude/skills/personal_background.md`
   - Both quiz type guides:
     - `.claude/skills/en-lesson-quiz-generate/references/cloze_deletion.md`
     - `.claude/skills/en-lesson-quiz-generate/references/multiple_choice.md`
3. Identify the **chapters** in the lesson (sections separated by `---`, skipping Material). Number them starting at 1.
4. Parse the **Vocabulary** section to extract all words/phrases with their definitions and sentences.
5. For **each chapter**, generate N quizzes (one per vocabulary word):
   - Assign each word to either cloze or multiple choice (40/60 split per chapter)
   - Set `section` and `section_name` to match the chapter index and title
   - Ensure each chapter's quizzes test the same words but with different questions
6. Collect all questions into a single flat JSON array (all chapters combined, ordered chapter by chapter).
7. Save to `data/quiz/{channel_slug}/{lesson_filename}.json`. Create directories if needed.

---

## Unified Quiz Fields

Every quiz object must include:

| Field | Type | Description |
|-------|------|-------------|
| `lesson_title` | str | Video title from the Material section |
| `section` | str | Chapter number as string, e.g. `"1"`, `"2"` |
| `section_name` | str | Chapter heading, e.g. `"Vocabulary"`, `"Story"` |
| `quiz_format` | str | One of: `cloze_deletion`, `multiple_choice` |
| `vocabulary_word` | str | The vocabulary word/phrase being tested |

Additional fields per format are defined in the respective reference `.md` files.

---

## Save to JSON

Write all questions as a JSON array to `data/quiz/{channel_slug}/{lesson_filename}.json` (strip `.md` from the lesson filename). Use **Python via Bash** with `json.dump()` to write the JSON — this avoids escaping issues with quotes and special characters in definitions and sentences.

---

## Output

After saving, print the file path and a summary table:

```
Quiz saved: data/quiz/{channel_slug}/{filename}.json

| Chapter | Section Name | Cloze | MC | Total |
|---------|-------------|-------|----|-------|
| 1       | Vocabulary  | 8     | 13 | 21    |
| 2       | Story       | 8     | 13 | 21    |
| Total   |             | 16    | 26 | 42    |
```

---

## Rules

- Every vocabulary word gets exactly **one** quiz per chapter
- Each chapter's quizzes must be **distinct** — no duplicate questions across chapters
- Chapter 1 quizzes focus on **definition recall**, Chapter 2 on **contextual usage**
- Cloze sentences should provide enough context to recall the word
- Multiple choice distractors must be plausible — other vocabulary words from the same lesson make good distractors
- Every multiple choice explanation must say **WHY** an option is correct or incorrect
- Every question must be self-contained — the user may take the quiz days later
- Use the personal background to make application questions feel concrete and relevant
- Verify the lesson file exists before proceeding
