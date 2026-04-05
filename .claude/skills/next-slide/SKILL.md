---
name: next-slide
description: Fetch and display the next learning slide (chapter or quiz) and let the
  user take action inline. Use when user says "next slide", "next", "study", "learn",
  or "quiz me".
---

# Next Slide

Fetch the next slide and let the user interact with it in conversation.

## Setup

Run once at the start to load credentials. Extract from `.env` at project root and reuse for all subsequent calls:

```bash
TOKEN=$(grep WEBAPP_ACCESS_TOKEN .env | cut -d= -f2)
API=http://localhost:8999
```

If you get `{"detail":"Not authenticated"}`, regenerate the token:
```bash
cd backend && python3 -c "from src.auth import create_access_token; print(create_access_token({'username': 'alan'}))" && cd ..
```
Then update `WEBAPP_ACCESS_TOKEN` in `.env` with the new token.

## Step 1: Fetch Next Slide

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/api/slides/next"
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
curl -s -X POST -H "Authorization: Bearer $TOKEN" "$API/api/slides/chapters/{chapter_id}/learnt"
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

## Step 3: Submit Answer

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"round_num": N, "lesson_id": N, "user_answer": "ANSWER", "is_skip": false}' \
  "$API/api/slides/quizzes/{quiz_id}/respond"
```

For skip: `"is_skip": true`, `"user_answer": ""`.

Display result:
- **Correct/Incorrect** — show `is_correct`
- **MC quizzes**: show the `response_to_user_option_{a|b|c|d}` from `quiz_metadata` matching the user's chosen option
- **Non-MC quizzes**: show `good_points` and `bad_points` lists if present. If wrong, show `expected_answer`.
- **Takeaway**: show `quiz_take_away`
- If `round_done` is true, tell the user this revision round is complete

Then auto-fetch next slide (back to Step 1).
