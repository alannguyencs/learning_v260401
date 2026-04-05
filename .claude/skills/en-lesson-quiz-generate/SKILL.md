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

## Quiz Count — Flexible, Based on Vocabulary

The number of quizzes is determined by the vocabulary words in the lesson, **not a fixed count**.

**Formula:**
- Count the total vocabulary words/phrases (N) from the Vocabulary section tables
- Generate **N quizzes total** (one per vocabulary word)
- Split roughly: **40% cloze deletion, 60% multiple choice** (round as needed)
- Cloze deletions test **word recall** — can the user fill in the vocabulary word given a context sentence?
- Multiple choice questions test **word meaning** — can the user pick the correct definition, usage, or identify the word from a description?

**Example:** 21 vocabulary words → 8 cloze + 13 multiple choice = 21 quizzes

---

## Instructions

1. Parse `$ARGUMENTS` to extract the **lesson file path**.
2. Read the following files **in parallel**:
   - The lesson file at the extracted path
   - The user's background at `.claude/skills/personal_background.md`
   - Both quiz type guides:
     - `.claude/skills/en-lesson-quiz-generate/references/cloze_deletion.md`
     - `.claude/skills/en-lesson-quiz-generate/references/multiple_choice.md`
3. Parse the **Vocabulary** section to extract all words/phrases with their definitions and sentences.
4. Assign each vocabulary word to either cloze or multiple choice (40/60 split). Ensure variety — don't put all nouns in one format.
5. Generate quizzes:
   - **Cloze deletion**: Use the sentence from the vocabulary table (or a new sentence) with the vocabulary word blanked out.
   - **Multiple choice**: Test definition knowledge, correct usage in context, or identifying the word from a description. Spread across cognitive levels (recall, understanding, application).
6. Collect all questions into a single flat JSON array.
7. Save to `data/quiz/{channel_slug}/{lesson_filename}.json`. Create directories if needed.

---

## Unified Quiz Fields

Every quiz object must include:

| Field | Type | Description |
|-------|------|-------------|
| `lesson_title` | str | Video title from the Material section |
| `section` | str | Always `"1"` (Vocabulary section) |
| `section_name` | str | Always `"Vocabulary"` |
| `quiz_format` | str | One of: `cloze_deletion`, `multiple_choice` |
| `vocabulary_word` | str | The vocabulary word/phrase being tested |

Additional fields per format are defined in the respective reference `.md` files.

---

## Save to JSON

Write all questions as a JSON array to `data/quiz/{channel_slug}/{lesson_filename}.json` (strip `.md` from the lesson filename). Use **Python via Bash** with `json.dump()` to write the JSON — this avoids escaping issues with quotes and special characters in definitions and sentences.

---

## Output

After saving, print the file path and a summary:

```
Quiz saved: data/quiz/{channel_slug}/{filename}.json

Vocabulary words: {N}
Cloze deletion:   {count}
Multiple choice:  {count}
Total quizzes:    {total}
```

---

## Rules

- Every vocabulary word gets exactly **one** quiz question
- Do NOT generate duplicate or near-duplicate questions
- Cloze sentences should provide enough context to recall the word
- Multiple choice distractors must be plausible — other vocabulary words from the same lesson make good distractors
- Every multiple choice explanation must say **WHY** an option is correct or incorrect
- Every question must be self-contained — the user may take the quiz days later
- Use the personal background to make application questions feel concrete and relevant
- Verify the lesson file exists before proceeding
