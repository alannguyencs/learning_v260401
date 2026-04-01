# Free Recall Quiz — Generation Guide

## What it is

The user sees a prompt and writes down **everything they remember** about that section topic — unprompted, no hints, no options. It forces active retrieval from memory, which is the strongest form of learning reinforcement.

## Rules

1. The question must be **open-ended** — ask the user to recall the key ideas of the section without giving away what those ideas are.
2. Do NOT embed any content from the section in the question stem. The whole point is cold retrieval.
3. `key_points` must list the 3–5 most important facts, principles, or insights from the section. These are the scoring criteria — a good answer covers most of them.
4. `model_answer` is a complete, well-written answer that hits all key points. It is shown to the user after they attempt the recall.
5. Tailor the question to the section name — e.g., for a "Recommendation" section, ask what the recommended action steps were.

## JSON Schema

```json
{
  "lesson_title": "Title from metadata JSON",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "free_recall",
  "question": "Without looking at the lesson, write down everything you remember from the [Section Name] section. What were the key ideas?",
  "key_points": [
    "Key point 1 — a core fact or insight from this section",
    "Key point 2",
    "Key point 3"
  ],
  "model_answer": "A complete answer would include: [full model answer covering all key points in natural prose]",
  "quiz_take_away": "One sentence summarising the most important thing this section teaches"
}
```

## Example

```json
{
  "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "free_recall",
  "question": "Without looking at the lesson, write down everything you remember from the Summary section. What were the main What, Why, and How points?",
  "key_points": [
    "$5K/year in S&P 500 from your 20s grows to $1.4M at retirement",
    "Only 4% of students can monetize their passion — build passion through mastery instead",
    "Panic-selling in 2008 and refusing to re-enter permanently cost 40% of net worth",
    "FBI framework: fund Emergency → Essentials → Equity → Enjoyment in order",
    "H = O/D: happiness = what you own divided by what you desire"
  ],
  "model_answer": "The Summary covers 20 life cheat codes across money, career, and mindset. On money: invest $5K/year in an S&P 500 index fund and never sell — panic-selling in 2008 cost 40% of net worth permanently. Use the FBI framework (Emergency → Essentials → Equity → Enjoyment) and avoid status debt. On career: chase equity over salary, get a mentor before 40, and move where the action is. On mindset: only 4% of students can monetise their passion, so build mastery first. The monk's happiness equation sums it up: H = O/D — manage your desires, not just your possessions.",
  "quiz_take_away": "Active retrieval of the What/Why/How structure cements the lesson's core framework in memory"
}
```
