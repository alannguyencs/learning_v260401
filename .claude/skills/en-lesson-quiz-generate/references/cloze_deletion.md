# Cloze Deletion Quiz — English Vocabulary

## What it is

A sentence has the **vocabulary word removed** and replaced with `___`. The user fills in the blank from memory. It tests whether the user can **recall the correct English word** given a meaningful context.

## Rules

1. The sentence should provide enough context (a definition hint, a situational clue, or a spatial relationship) so that someone who learned the word can recall it.
2. Prefer using the **original transcript sentence** from the vocabulary table. If the original sentence is too short or lacks context (e.g., "It's a ___."), create a new sentence that provides better clues.
3. Remove only the **vocabulary word** — not articles, prepositions, or surrounding words.
4. `blanks` is an ordered list of the correct word(s) matching each `___`.
5. `context_hint` is optional — use it only when the blank is ambiguous without a nudge (e.g., "furniture" or "part of the room").

## JSON Schema

```json
{
  "lesson_title": "Video title",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "cloze_deletion",
  "vocabulary_word": "the word being tested",
  "sentence": "A lamp hangs from the ___ of the room.",
  "blanks": ["ceiling"],
  "context_hint": "the top surface of a room",
  "quiz_take_away": "One sentence reinforcing the word's meaning"
}
```

## Example 1 — Noun from transcript

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "cloze_deletion",
  "vocabulary_word": "ceiling",
  "sentence": "A lamp hangs from the ___ of the room.",
  "blanks": ["ceiling"],
  "context_hint": "the top surface of a room",
  "quiz_take_away": "The ceiling is the top interior surface of a room — opposite of the floor"
}
```

## Example 2 — Verb with new sentence

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "cloze_deletion",
  "vocabulary_word": "rings",
  "sentence": "The alarm clock ___ every day at 7 o'clock to wake me up.",
  "blanks": ["rings"],
  "context_hint": "",
  "quiz_take_away": "To ring means to make a sound — used for alarms, bells, and phones"
}
```

## Example 3 — Compound noun

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "cloze_deletion",
  "vocabulary_word": "remote control",
  "sentence": "I can't find the ___. How do I change the TV channel?",
  "blanks": ["remote control"],
  "context_hint": "a device to operate electronics from a distance",
  "quiz_take_away": "A remote control lets you operate a TV or other electronics without getting up"
}
```
