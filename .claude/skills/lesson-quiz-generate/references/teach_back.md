# Teach-Back / Feynman Quiz — Generation Guide

## What it is

The user explains a concept from the section **as if teaching it to someone who has never heard of it**. This is the Feynman Technique: if you can teach it simply, you truly understand it. If you can't, the gaps become visible.

## Rules

1. Target **one specific concept** from the section — not the whole section. Pick the most important or most commonly misunderstood idea.
2. The question must name the concept to explain but give no hints about what the explanation should contain.
3. `key_elements` lists the 2–4 components a strong explanation must include (e.g., the mechanism, a concrete example, why it matters).
4. `model_answer` is a clear, plain-English explanation that a non-expert could follow. It should avoid jargon and use an analogy where helpful.
5. Choose concepts that have a non-obvious "why" — things that feel simple on the surface but require genuine understanding to explain well.

## JSON Schema

```json
{
  "lesson_title": "Title from metadata JSON",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "teach_back",
  "question": "Explain [specific concept] as if you were teaching it to a friend who has never heard of it. Use plain language and an example if it helps.",
  "key_elements": [
    "Element 1 — what a strong explanation must include",
    "Element 2",
    "Element 3"
  ],
  "model_answer": "A good explanation would go something like this: [plain-language explanation with analogy or example]",
  "quiz_take_away": "One sentence on what genuine understanding of this concept looks like"
}
```

## Example

```json
{
  "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "teach_back",
  "question": "Explain the H = O/D happiness equation as if you were teaching it to a friend who has never heard of it. Use plain language and an example if it helps.",
  "key_elements": [
    "H = Own ÷ Desire — happiness is a ratio, not an absolute amount",
    "Happiness increases when you own more than you desire, or when you reduce desires",
    "Desires can grow infinitely; possessions are always finite — so managing desires is more powerful than accumulating more",
    "When desires approach zero, happiness approaches infinity"
  ],
  "model_answer": "The equation H = O/D says happiness equals what you own divided by what you desire. Think of it like a fraction: if your desires are the denominator, making it smaller — even if the numerator stays the same — makes the result bigger. Say you own a modest flat in Hong Kong and your only desire is to have a home for your family — you are content. But if you start desiring a bigger flat, a car, a holiday, the denominator grows and happiness shrinks even though nothing in your life actually got worse. The monk's insight is that desire is the variable you can actually control — and when desires shrink toward zero, the fraction approaches infinity.",
  "quiz_take_away": "Happiness is a ratio you can manage by controlling the denominator (desire), not just the numerator (what you own)"
}
```
