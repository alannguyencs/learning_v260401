# Slide Stack

## 4 Content Layers

Content is organized in a four-level hierarchy: a **book** is the top-level grouping that scopes a subject or course (e.g. `nutrition_and_diet`, `sleep_and_circadian_rhythm`); each book contains **lessons**, which represent a single topic or principle within that subject (e.g. `13_emphasize_nutrient_density_over_caloric_quantity.md`); each lesson is broken into **chapters** — the `## Summary`, `## Recommendation`, and `## Story` sections — which are the atomic reading units delivered to the user one at a time; and each chapter has associated **quizzes** that test recall of the chapter material. In short, books scope the content, lessons group related ideas, chapters deliver knowledge, and quizzes enforce retrieval practice.

```
Book                        Lesson                          Chapter         Quiz
(folder)                    (file)                          (section)

nutrition_and_diet/    +--> 13_emphasize_nutrient_...md +--> ## Summary  +--> Q1, Q2
                       |                                +--> ## Recommend+--> Q3, Q4
                       |                                +--> ## Story    +--> Q5, Q6
                       |
                       +--> 14_recognize_nutrition_...md +--> ## Summary  +--> ...
                       |                                +--> ## Recommend+--> ...
                       |                                +--> ## Story    +--> ...
                       |
sleep_and_circadian/   +--> 01_prioritize_lufts_...md   +--> ...
                       +--> 02_understand_sleep_...md    +--> ...
```

## 4 Quiz Types

Each chapter generates 9 quiz questions across four formats designed for beginner-level spaced-repetition. **Free recall** asks the user to write what they remember about a specific topic from the chapter — cold retrieval with no hints. **Teach-back** asks the user to explain one key concept in their own words, testing understanding rather than rote memory. **Cloze deletion** presents an actual sentence from the lesson with a key term blanked out for the user to fill in. **Multiple choice** offers four options (A–D); out of 5 MC questions per chapter, 4 are single-answer and 1 is multi-answer ("Select all that apply"). Open-ended formats (free recall and teach-back) are graded by AI; multiple choice is auto-graded by exact match.

```
Chapter (e.g. ## Summary)
  |
  +--> 1x Free recall       "What do you remember about [topic]?"
  +--> 1x Teach-back         "In your own words, explain why [concept] matters."
  +--> 2x Cloze deletion     "Sentence with ___ replacing a key term."
  +--> 5x Multiple choice    4 single-answer + 1 multi-answer
  |
  = 9 quizzes per chapter
  = 27 quizzes per lesson (3 chapters)
```

## Slide Stack

### Problem

After authentication, users have no way to consume lesson content, take quizzes, or engage with the spaced-repetition system. The backend content and revision infrastructure exists but has no frontend consumer.

### Solution

A continuous slide stream combining chapter study and spaced-repetition quizzes. The user sees one slide at a time: either a chapter to read or a quiz to answer. A strict 2-tier priority algorithm controls slide order: due revision quizzes always come before new chapters. The quiz loop for a lesson only activates once all its chapters have been learnt. Within revision quizzes, unskipped quizzes are served weakest-recall-first; skipped quizzes form a back-of-queue. Quizzes from all due lessons are pooled together — there is no per-lesson quiz isolation. Open-ended quiz answers are graded by AI. Users can navigate back and forward through their slide history. A floating chat icon on each slide lets the user ask contextual questions, answered by AI using the lesson source material, slide content, and conversation history.

```
                          +---------------------------+
                          |       SLIDE STREAM        |
                          |   one slide at a time     |
                          +-------------+-------------+
                                        |
                   +--------------------+--------------------+
                   |                                         |
          +--------v--------+                       +--------v--------+
          |  ChapterSlide   |                       |   QuizSlide     |
          |  read & learn   |                       |  answer & grade |
          +-----------------+                       +-----------------+
                                                    |  MC: auto-grade |
                                                    |  Open: AI-grade |
                                                    +-----------------+

```

### User Flow

```
User logs in -> redirected to /slides
  |
  v
BookSelector: All Books | select a specific book
  |
  v
SlidePage fetches current slide
  |
  +-- Chapter slide:
  |     User reads content
  |     [Mark as Learnt] -> records progress
  |     [Down arrow]     -> marks learnt and moves to next slide
  |
  +-- Quiz slide (revision round):
  |     User answers MC or open-ended question
  |     [Submit Answer] -> correct/incorrect badge + feedback
  |     [Next Slide]    -> advances after feedback
  |     [Skip]          -> quiz goes to back of queue
  |
  +-- Navigation:
  |     [Up arrow]   -> go to previous slide in history
  |     [Down arrow] -> go to next slide (replays forward history first)
  |
  +-- All caught up:
        Message shown when no slides remain
```

### Foundational Rules

- Chapters within a lesson are presented in sequence (Summary → Recommendation → Story)
- Lessons within a book are presented in sequence (lesson 1 before lesson 2, etc.)
- A quiz slide can only appear after its corresponding chapter slide has been learnt
- Chapters and lessons across different books may be mixed — there is no cross-book ordering guarantee

```
Book A                              Book B
──────────────────────────          ──────────────────────────
Lesson 1 (sequential)              Lesson 1 (sequential)
  Ch1 → Quiz → Ch2 → Quiz → Ch3     Ch1 → Quiz → Ch2 → Quiz
         ↓                                  ↓
Lesson 2 (sequential)              Lesson 2 (sequential)
  Ch1 → Quiz → Ch2 → Quiz           Ch1 → Quiz → Ch2 → Quiz
         ↓                                  ↓
Lesson 3 ...                       Lesson 3 ...

       \                                  /
        \________________________________/
                       |
              Books may interleave:
     A:L1:Ch1 → B:L1:Ch1 → A:L1:Ch2 → B:L1:Ch2 → ...
```

### 2-Tier Stacking Algorithm

**Foundational theory:** Spaced Repetition Systems (SRS) — see section 2.1 in [260324_time_framed_learning.md](./260324_time_framed_learning.md). In practice, the slide stack replaces the counting of "days" with the counting of "lessons learnt" as the spacing unit, so revision rounds are triggered by learning progress rather than calendar time.

- **Revision rounds (R0, R1, R2, ...)** are successive passes over a lesson's quizzes. R0 is created as soon as the first chapter in a lesson is marked as learnt, and accumulates quizzes as more chapters are learnt. A round is considered **finished** when both: (1) all chapters in the lesson are marked as learnt, and (2) more than 50% of the lesson's total quizzes have been answered (skipped quizzes do not count as answered).
- **A lesson is "learnt"** when both conditions are met: (1) all chapters in that lesson have been marked as learnt by the user, and (2) the first revision round R0 is completed (>50% of quizzes answered). Each time a lesson becomes fully learnt, the global `lesson_count` increments by 1. This counter is the system's clock — it measures progress in units of completed lessons, not calendar time. *Remark: condition (2) is not yet implemented — currently `lesson_count` increments immediately when the last chapter is marked learnt, without waiting for R0 completion.*
- **A revision quiz is "due"** when the current `lesson_count` has reached or passed the round's `due_at_lesson_count`. Revision rounds are scheduled at exponentially increasing intervals after completion: R0 completes → R1 due in +2 lessons, R1 → R2 in +4, R2 → R3 in +8, and so on (`due_at = lesson_count_when_completed + 2^(round_num + 1)`). A round that is due but not yet completed surfaces its quizzes in Tier 1.

The slide stacking algorithm decides which slide to show next. It enforces a strict priority: due revision quizzes always come before new chapters. This ensures the user revisits material at the right time before consuming anything new.

**Tier 1 — Revision quizzes** pools quizzes from all due lessons together (no per-lesson isolation). Within the pool, unskipped quizzes (Group A) are served weakest-recall-first using the spaced-repetition memory score m(t). Skipped quizzes (Group B) sit in a back-of-queue and do not block Tier 2 — they resurface via a retry cycle once all non-skipped quizzes are exhausted. The quiz loop for a lesson only activates once every chapter in that lesson has been marked as learnt (the activation gate).

**Tier 2 — New chapters** only fires when Group A is empty. It picks the next unlearnt chapter, optionally filtered by book. If no book is selected, it picks randomly across all books.

When both tiers are empty, the user sees "All caught up."

```
SlideSelector.get_next_slide(username, book_id)
  |
  v
+=====================================================+
| TIER 1: REVISION QUIZZES (always checked first)     |
|                                                     |
|  Activation gate: ALL chapters in lesson learnt?    |
|       No  --> skip this lesson's quizzes            |
|       Yes --> pool its due quizzes                  |
|                                                     |
|  +-----------------------------------------------+ |
|  | Group A: unskipped quizzes                     | |
|  |   sort by m(t) weakest recall first            | |
|  |   any found? --> return QuizSlide (BLOCKS T2)  | |
|  +-----------------------------------------------+ |
|                     |                               |
|                     v  Group A empty?               |
|  +-----------------------------------------------+ |
|  | Retry cycle: answered/total > 50%?             | |
|  |   No  --> clear skip log, quizzes return to A  | |
|  |   Yes --> round complete, schedule next round   | |
|  +-----------------------------------------------+ |
|                     |                               |
|                     v                               |
|  +-----------------------------------------------+ |
|  | Group B: skipped quizzes                       | |
|  |   oldest skip first                            | |
|  |   does NOT block Tier 2                        | |
|  +-----------------------------------------------+ |
+=====================================================+
                      |
                      v  Group A empty
+=====================================================+
| TIER 2: NEW CHAPTER                                 |
|                                                     |
|  book_id set? --> next unlearnt chapter in book      |
|  no book_id?  --> random pick across all books       |
|                                                     |
|  found? --> return ChapterSlide                     |
+=====================================================+
                      |
                      v  both empty
              "All caught up"
```

### Scope

**Included:**
- Chapter reading + mark-as-learnt interaction
- MC and open-ended quiz answering
- AI-graded PASSED/FAILED with itemized good/bad points
- Book filtering via dropdown
- Spaced-repetition round display (Revision R0, R1, ...)
- All-caught-up state
- Contextual AI Q&A chat on chapter and quiz slides
- Back/forward navigation through slide history
- Activity log (accessible via Activity tab on the main `/dashboard`)
- Per-book learning progress with accuracy trendline (accessible via Learning tab on the main `/dashboard`)

**Not included:**
- None (slide dashboard has been merged into the main `/dashboard`)

## References

- MEMORIZE Algorithm — [Enhancing Human Learning via Spaced Repetition Optimization (PNAS 2019)](https://www.pnas.org/doi/10.1073/pnas.1815156116)
- Spaced Repetition Systems (SRS) — section 2.1 in [260324_time_framed_learning.md](./260324_time_framed_learning.md) [[11](https://science.lpnu.ua/sisn/all-volumes-and-issues/volume-18-part-2-2025/adaptive-learning-algorithms-mobile-application)][[12](https://journals.zeuspress.org/index.php/IJASSR/article/view/425)][[13](https://pmc.ncbi.nlm.nih.gov/articles/PMC6410796/)][[14](https://www.pnas.org/content/pnas/116/10/3988.full.pdf)]
- Retrieval Practice (The Testing Effect) — section 2.2 in [260324_time_framed_learning.md](./260324_time_framed_learning.md) [[15](https://pmc.ncbi.nlm.nih.gov/articles/PMC7821628/)][[16](https://pmc.ncbi.nlm.nih.gov/articles/PMC6990689/)][[17](https://pmc.ncbi.nlm.nih.gov/articles/PMC8866974/)][[18](https://www.pnas.org/doi/pdf/10.1073/pnas.2413511121)]
- Interleaved Practice — section 2.3 in [260324_time_framed_learning.md](./260324_time_framed_learning.md) [[20](https://pmc.ncbi.nlm.nih.gov/articles/PMC10482805/)][[21](https://pmc.ncbi.nlm.nih.gov/articles/PMC4141442/)][[22](https://journals.sagepub.com/doi/10.1177/09567976211057507)][[23](https://pmc.ncbi.nlm.nih.gov/articles/PMC8476370/)][[24](https://www.frontiersin.org/articles/10.3389/fpsyg.2014.00936/pdf)]
