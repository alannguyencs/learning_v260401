# Multiple Choice Quiz — English Vocabulary

## What it is

A question with **4 options (A, B, C, D)** where one option is correct. Tests whether the user knows the **meaning, usage, or identification** of a vocabulary word.

## Question Styles

Vary across these styles to keep quizzes engaging:

1. **Definition → Word**: "Which word means ___?" (options are vocabulary words)
2. **Word → Definition**: "What does ___ mean?" (options are definitions)
3. **Sentence context**: "Which word best completes: '___'?" (options are vocabulary words)
4. **Odd one out**: "Which word does NOT belong to the category of ___?" (options are vocabulary words)
5. **Application**: "You need to ___. Which item would you use?" (options are vocabulary words)

## Rules

1. Always generate exactly **4 options (A, B, C, D)**.
2. All questions are **single-answer** (`["B"]`) — one correct option.
3. Use **other vocabulary words from the same lesson** as plausible distractors where possible.
4. Each `response_to_user_option_*` must explain **WHY** that option is correct or incorrect — include the word's actual definition.
5. **Every question must be self-contained.** The user may take the quiz days later.
6. Spread across cognitive levels: recall (what does it mean?), understanding (why this word?), application (when would you use it?).

## JSON Schema

```json
{
  "lesson_title": "Video title",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "multiple_choice",
  "quiz_type": "recall",
  "vocabulary_word": "the word being tested",
  "question": "The question text",
  "quiz_learnt": "What the user is learning from this question",
  "option_a": "Option A text",
  "option_b": "Option B text",
  "option_c": "Option C text",
  "option_d": "Option D text",
  "correct_options": ["B"],
  "response_to_user_option_a": "Explanation for why A is correct or incorrect",
  "response_to_user_option_b": "Explanation for why B is correct or incorrect",
  "response_to_user_option_c": "Explanation for why C is correct or incorrect",
  "response_to_user_option_d": "Explanation for why D is correct or incorrect",
  "quiz_take_away": "Key takeaway reinforcing the vocabulary word"
}
```

## Example 1 — Definition → Word (recall)

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "multiple_choice",
  "quiz_type": "recall",
  "vocabulary_word": "wardrobe",
  "question": "Which word means 'a tall cabinet for storing clothes'?",
  "quiz_learnt": "The definition of wardrobe",
  "option_a": "Dresser",
  "option_b": "Wardrobe",
  "option_c": "Drawer",
  "option_d": "Wastebasket",
  "correct_options": ["B"],
  "response_to_user_option_a": "Incorrect. A dresser is also furniture with drawers, but it is lower and wider — not a tall cabinet you hang clothes in.",
  "response_to_user_option_b": "Correct. A wardrobe is a tall cabinet where you store clothes, often with a hanging rail inside.",
  "response_to_user_option_c": "Incorrect. A drawer is a sliding box inside a dresser or desk — it's a component, not a standalone cabinet.",
  "response_to_user_option_d": "Incorrect. A wastebasket is a small bin for throwing away trash.",
  "quiz_take_away": "A wardrobe is a tall standing cabinet for clothes — different from a dresser which is shorter with drawers"
}
```

## Example 2 — Application (understanding)

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "multiple_choice",
  "quiz_type": "application",
  "vocabulary_word": "light switch",
  "question": "You walk into a dark room and want to turn on the light. What do you look for on the wall?",
  "quiz_learnt": "The practical use of a light switch",
  "option_a": "A remote control",
  "option_b": "A poster",
  "option_c": "A light switch",
  "option_d": "A window sill",
  "correct_options": ["C"],
  "response_to_user_option_a": "Incorrect. A remote control operates a TV or electronics from a distance — it's not mounted on the wall.",
  "response_to_user_option_b": "Incorrect. A poster is a decorative picture on the wall — it doesn't control lighting.",
  "response_to_user_option_c": "Correct. A light switch is a button or lever on the wall that turns the room light on or off.",
  "response_to_user_option_d": "Incorrect. A window sill is the flat shelf at the bottom of a window — it's for placing objects, not controlling lights.",
  "quiz_take_away": "A light switch is the wall-mounted control for room lighting — you flip it to turn lights on or off"
}
```

## Example 3 — Sentence context (understanding)

```json
{
  "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
  "section": "1",
  "section_name": "Vocabulary",
  "quiz_format": "multiple_choice",
  "quiz_type": "understanding",
  "vocabulary_word": "hangs",
  "question": "Which word best completes this sentence? 'A lamp ___ from the ceiling of the room.'",
  "quiz_learnt": "The verb 'hangs' means to be suspended from above",
  "option_a": "rings",
  "option_b": "hangs",
  "option_c": "comfortable",
  "option_d": "above",
  "correct_options": ["B"],
  "response_to_user_option_a": "Incorrect. 'Rings' means to make a sound (like an alarm) — a lamp doesn't make sounds.",
  "response_to_user_option_b": "Correct. 'Hangs' means to be attached from above and suspended — a ceiling lamp hangs from the ceiling.",
  "response_to_user_option_c": "Incorrect. 'Comfortable' is an adjective meaning giving physical ease — it doesn't describe how a lamp is attached.",
  "response_to_user_option_d": "Incorrect. 'Above' is a preposition meaning higher than — it doesn't work as the verb in this sentence.",
  "quiz_take_away": "To hang means to be suspended or attached from above — used for lamps, pictures, curtains, and more"
}
```
