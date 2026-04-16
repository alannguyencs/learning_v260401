---
name: en-lesson-create-vocab
description: Generate an English vocabulary lesson from a curated transcript file (sentences the user kept because they contain new vocabulary). Use when the user wants to create a vocab lesson from a transcript in data/transcript/.
argument-hint: "[path-to-curated-transcript.md]"
allowed-tools: Bash, Read, Write
---

# English Vocabulary Lesson from Curated Transcript

Given a curated transcript file, extract new vocabulary and generate a structured English vocabulary lesson.

## Workflow Context

This skill is step 3 in the transcript-to-lesson pipeline:
1. `/en-dl-youtube-transcript` — download full transcript
2. User manually removes sentences they already understand
3. **This skill** — generate a vocabulary lesson from the remaining sentences

## Input

The user argument is: $ARGUMENTS

This is a path to a curated transcript markdown file. The file has this structure:

```markdown
# {Video Title}

- **Video:** [{Video Title}](https://www.youtube.com/watch?v={VIDEO_ID})
- **Channel:** {Channel Name}
- **Published:** {YYYY-MM-DD}

---

{sentence 1}
{sentence 2}
...
```

## Execution Flow

### Phase 1: Read inputs (parallel)

Read these two files **in parallel** (same message, two Read calls):

```
Call 1: Read the curated transcript file (from user argument)
Call 2: Read .claude/skills/personal_background.md
Call 3: Read .claude/skills/lesson-create-english-vocab/lesson_template.md
```

### Phase 2: Extract vocabulary

From the curated sentences, identify the **new vocabulary words** — the reason the user kept each sentence. These are typically:
- Nouns for objects/places (e.g. "window sill", "curtains", "wardrobe", "dresser")
- Adjectives describing properties (e.g. "comfortable", "colorful")
- Verbs for actions (e.g. "rings", "hangs")
- Prepositions/phrases for spatial relationships (e.g. "in front of", "next to", "in the middle of")

**Judgment rules:**
- Common words like "my", "is", "the", "there" are NOT new vocabulary — skip them
- If a sentence has multiple potential new words, include all of them
- Compound nouns count as one entry (e.g. "alarm clock", "window sill", "light switch", "remote control")
- Group words by theme/category when possible

### Phase 3: Generate lesson file

Use the **Write tool** (not Bash) to create the lesson at:

```
data/lesson/{channel_slug}/{yymmdd}_{slug}_vocab.md
```

The `{channel_slug}`, `{yymmdd}`, and `{slug}` are derived from the transcript file's header metadata, using the same naming convention as `lesson-create-youtube`:
- `{channel_slug}` — channel name: lowercased, spaces → `_`, special chars removed
- `{yymmdd}` — from published date
- `{slug}` — from video title: lowercased, spaces → `_`, special chars removed, max 50 chars, no trailing underscores

Append `_vocab` to distinguish from a regular lesson on the same video.

Read `.claude/skills/lesson-create-english-vocab/lesson_template.md` for the section structure and examples.

### Phase 4: Display summary

After saving the file, display:

```
Lesson saved: data/lesson/{channel_slug}/{yymmdd}_{slug}_vocab.md

Title:       {video title}
Channel:     {channel name}
Vocabulary:  {count} words/phrases
Sentences:   {count} curated sentences
```

## Rules

1. Use the **transcript sentences** as the primary source — every vocabulary word must appear in at least one curated sentence
2. Read `.claude/skills/personal_background.md` to personalize the Story section
3. Always `mkdir -p data/lesson/{channel_slug}` before writing files
4. Use the **Write tool** to create the lesson markdown
5. The Story must use **every** vocabulary word at least once
6. Keep definitions simple and clear — this is for a non-native English learner
