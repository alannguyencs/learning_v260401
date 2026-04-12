# Multiple Choice Quiz — Generation Guide

## What it is

A question with **4 options (A, B, C, D)** where one or more options are correct. It tests a range of cognitive levels — from recall to analysis — and forces the user to discriminate between plausible alternatives.

## Rules

1. Always generate exactly **4 options (A, B, C, D)**.
2. Alternate between **single-answer** (`["B"]`) and **multiple-answer** (`["A", "C"]`) questions across the 5 questions in a section. For multiple-answer questions, append **"Select all options that apply."** to the end of the question text so the user knows more than one answer may be correct.
3. Test **deep understanding**, not surface-level keyword matching. Distractors must be plausible — wrong for a specific, explainable reason.
4. Each `response_to_user_option_*` must explain **WHY** that option is correct or incorrect — not just restate it.
5. **Every question must be self-contained.** The user may take the quiz weeks after reading the lesson. Embed any necessary context (character names, specific examples, story details) directly in the question stem or options.
6. Spread the 5 questions across different cognitive levels — aim for at least one each of: recall, understanding, application, and analysis across the 5 questions.

## Cognitive Levels

- **recall** — factual memory of key concepts, numbers, or terms from the section
- **understanding** — comprehension of why/how a concept works
- **application** — applying the concept to a new scenario
- **analysis** — breaking down and evaluating a complex situation

## JSON Schema

```json
{
  "lesson_title": "Title from metadata JSON",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "multiple_choice",
  "quiz_type": "understanding",
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
  "quiz_take_away": "Key takeaway from this question"
}
```

## Suggested Distribution for 5 Questions per Section

| Question | Cognitive Level | Answer Mode |
|----------|----------------|-------------|
| 1 | recall | single |
| 2 | understanding | multiple |
| 3 | application | single |
| 4 | understanding | multiple |
| 5 | analysis | single |

Adapt as needed — if the section has no actionable content, skip application and add understanding.

## Example

```json
{
  "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "multiple_choice",
  "quiz_type": "understanding",
  "question": "An investor puts $5,000/year into an S&P 500 index fund starting at age 25. During a market crash at age 40, she panics and withdraws everything, then refuses to re-enter the market. What is the most likely long-term consequence described in the lesson?",
  "quiz_learnt": "Why staying in the market through crashes matters more than timing it",
  "option_a": "She loses only the money she withdrew; future earnings are unaffected",
  "option_b": "Her net worth ends up permanently lower — by approximately 40% — compared to doing nothing",
  "option_c": "She avoids the crash entirely and can re-enter at a lower price, coming out ahead",
  "option_d": "The impact is negligible because index funds always recover within 6 months",
  "correct_options": ["B"],
  "response_to_user_option_a": "Incorrect. The lesson is explicit: refusing to re-enter the market after the crash caused permanent damage, not just the initial withdrawal loss.",
  "response_to_user_option_b": "Correct. The speaker's own experience: panic-sold in 2008, refused to re-enter when the market bounced back, and net worth ended up 40% lower than if he had done nothing.",
  "response_to_user_option_c": "Incorrect. This assumes rational re-entry at the bottom — but the lesson describes the opposite: the investor refused to go back in even as the market recovered.",
  "response_to_user_option_d": "Incorrect. The lesson does not say funds recover in 6 months. The damage here is behavioural — the investor locked in losses by refusing to stay in.",
  "quiz_take_away": "Panic-selling turns a temporary paper loss into a permanent one — staying in the market is the hard part, and the most important part"
}
```
