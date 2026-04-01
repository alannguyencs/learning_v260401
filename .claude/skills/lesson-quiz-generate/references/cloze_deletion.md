# Cloze Deletion Quiz — Generation Guide

## What it is

A sentence from the section has **one or more key terms removed**, replaced with `___`. The user fills in the blank(s) from memory. It targets recall of the **key terminology and coined concepts** introduced in the lesson — the named frameworks, metaphors, and defined terms that carry the lesson's meaning.

## Rules

1. Generate **2 cloze deletions per section** — each targeting a **different key term**.
2. Focus exclusively on **terminology** — named frameworks, coined phrases, defined concepts, or labelled steps introduced in the lesson (e.g., "FBI framework", "jobless recovery", "founder-market fit", "H = O/D"). Do NOT blank numbers, percentages, or statistics.
3. The sentence must come directly from the lesson content — do not invent new sentences.
4. Remove only the **term itself** — the label or name that a reader must have learned to fill in. The surrounding sentence should make the blank clearly answerable to someone who knows the lesson.
5. `blanks` is an ordered list of the correct term(s) matching each `___` in the sentence.
6. `context_hint` is optional — use it only when the term is ambiguous without additional framing.

## JSON Schema

```json
{
  "lesson_title": "Title from metadata JSON",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "cloze_deletion",
  "sentence": "To track and control spending, the lesson recommends building your own ___ — a personal financial system that categorises cash into Emergency, Essentials, Equity, and Enjoyment.",
  "blanks": ["FBI (Financial Bureau of Investigation)"],
  "context_hint": "",
  "quiz_take_away": "One sentence on why knowing this term matters"
}
```

## Example 1 — Named framework

```json
{
  "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "cloze_deletion",
  "sentence": "To track and control spending, the lesson recommends building your own ___ — a personal financial system that categorises cash into Emergency, Essentials, Equity, and Enjoyment.",
  "blanks": ["FBI (Financial Bureau of Investigation)"],
  "context_hint": "",
  "quiz_take_away": "The FBI framework gives spending a structure — you can only fund Enjoyment after the first three buckets are covered"
}
```

## Example 2 — Coined concept

```json
{
  "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
  "section": "1",
  "section_name": "Summary",
  "quiz_format": "cloze_deletion",
  "sentence": "The monk's happiness equation is ___, where happiness equals what you own divided by what you desire.",
  "blanks": ["H = O/D"],
  "context_hint": "",
  "quiz_take_away": "H = O/D frames happiness as a ratio — reducing desire is as powerful as gaining more"
}
```
