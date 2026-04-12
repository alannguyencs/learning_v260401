---
name: next-slide
description: Fetch and display the next learning slide (chapter or quiz) and let the
  user take action inline. Use when user says "next slide", "next", "study", "learn",
  or "quiz me".
---

# Next Slide

Fetch the next slide and let the user interact with it in conversation.

## Setup

Read `.env` at project root using the Read tool to extract `WEBAPP_ACCESS_TOKEN`. Use the literal token value in all curl commands (do NOT use subshells like `$(grep ...)` — they break permission pattern matching).

If you get `{"detail":"Not authenticated"}`, regenerate the token:
```bash
cd backend && python3 -c "from src.auth import create_access_token; print(create_access_token({'username': 'alan'}))" && cd ..
```
Then update `WEBAPP_ACCESS_TOKEN` in `.env` with the new token.

## Step 1: Fetch Next Slide

```bash
curl -s -H "Authorization: Bearer {TOKEN}" "http://localhost:8999/api/slides/next"
```

## Step 2: Display and Interact

### Chapter slide (`slide_type == "chapter"`)

Display:
```
**{book_title} / {lesson_title}**
**Chapter {chapter_index}: {title}**
---
{content rendered as markdown}
```

Ask: **"Mark as learnt?"** — wait for user confirmation.

On confirm, POST and display result:
```bash
curl -s -X POST -H "Authorization: Bearer {TOKEN}" "http://localhost:8999/api/slides/chapters/{chapter_id}/learnt"
```
- If `lesson_fully_learnt` is true, tell the user the lesson is complete
- Show `lesson_count`

Then auto-fetch next slide (back to Step 1).

### Quiz slide (`slide_type == "quiz"`)

Display:
```
**Quiz (Round {round_num}) — {book_title} / {lesson_title}**
Section: {section_name} | Type: {quiz_type}
---
{question}
```

For `multiple_choice`, show options. Check `correct_options` array length — if more than 1, note "*(Multiple correct answers possible)*":
```
- **A)** {option_a}
- **B)** {option_b}
- **C)** {option_c}
- **D)** {option_d}
```

For other quiz types (cloze, free_recall, teach_back), just show the question and let the user type a free-text answer.

Wait for user's answer (or "skip").

## Step 3: Evaluate and Submit Answer

### For skip:
```bash
curl -s -X POST -H "Authorization: Bearer {TOKEN}" -H "Content-Type: application/json" \
  -d '{"round_num": N, "lesson_id": N, "user_answer": "", "is_skip": true}' \
  "http://localhost:8999/api/slides/quizzes/{quiz_id}/respond"
```

### For actual answers — evaluate locally (do NOT rely on backend Gemini):

**You are the grader.** Compare the user's answer against the quiz data you already have (`expected_answer`, `correct_options`, `quiz_metadata`). Apply these grading rules:

- **multiple_choice**: Compare user's selected options against `correct_options`. `good_points`/`bad_points` = null.
- **cloze**: Check if the fill-in matches `expected_answer` or the `blanks` in `quiz_metadata`. Accept semantically equivalent answers. Generate `good_points`/`bad_points`.
- **free_recall / teach_back**: Check if the user covered the core concepts in `expected_answer`. Be lenient on wording, strict on concept correctness. Generate `good_points`/`bad_points`.

For `good_points`/`bad_points`, write each as one concise factual sentence (e.g. "The fill-in-the-blank word 'pillows' was correct." NOT "The student correctly...").

For non-MC quizzes, determine `is_correct`: correct if good_points ≥ 66% of total points.

Then submit with `pre_evaluated: true`:
```bash
curl -s -X POST -H "Authorization: Bearer {TOKEN}" -H "Content-Type: application/json" \
  -d '{"round_num": N, "lesson_id": N, "user_answer": "ANSWER", "is_skip": false, "pre_evaluated": true, "is_correct": BOOL, "good_points": ["..."], "bad_points": ["..."]}' \
  "http://localhost:8999/api/slides/quizzes/{quiz_id}/respond"
```

Display result:
- **Correct/Incorrect** — show `is_correct`
- **MC quizzes**: show the `response_to_user_option_{a|b|c|d}` from `quiz_metadata` matching the user's chosen option
- **Non-MC quizzes**: show `good_points` and `bad_points` lists if present. If wrong, show `expected_answer`.
- **Takeaway**: show `quiz_take_away`
- If `round_done` is true, tell the user this revision round is complete

Then auto-fetch next slide (back to Step 1).
