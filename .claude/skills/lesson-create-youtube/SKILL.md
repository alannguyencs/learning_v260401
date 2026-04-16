---
name: lesson-create-youtube
description: Fetch a YouTube video's metadata and transcript, save metadata as JSON, and generate a lesson note with 3 major sections + story. Use when the user provides a YouTube video URL.
argument-hint: "[youtube-video-url]"
allowed-tools: Bash, WebFetch, Write, Read
---

# YouTube Video to Lesson

Given a YouTube video URL, fetch its metadata and transcript, save the metadata as JSON, and generate a lesson markdown file with 3 major themed sections and a story.

## Input

The user argument is: $ARGUMENTS

Extract the video ID from the input. It may be provided as:
- A full URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- A short URL: `https://youtu.be/VIDEO_ID`
- Just the video ID: `VIDEO_ID`

## Execution Flow

### Phase 1: Fetch data (parallel)

Run these two Bash calls **in parallel** (same message, two tool calls):

```
Call 1: curl -s "https://www.youtube.com/watch?v={VIDEO_ID}" -o /tmp/yt_page.html
Call 2: youtube_transcript_api {VIDEO_ID} --format text
```

Read `.claude/skills/lesson-create-youtube/fetch.md` for extraction details and regex patterns.

### Phase 2: Extract metadata

Run a Python script via Bash to extract fields from the saved HTML. See `fetch.md` for the exact regex patterns and script.

### Phase 3: Save metadata JSON

Use Python `json.dump()` via Bash to write the JSON file. Read `.claude/skills/lesson-create-youtube/metadata_schema.md` for the schema and example.

Ensure the channel subdirectories exist first: `mkdir -p data/metadata/{channel_slug} data/lesson/{channel_slug}`

### Phase 4: Generate lesson file

Read the user's background at `.claude/skills/personal_background.md` — use it to personalize the **Story** section. The story does NOT need to be about the user. Use the user's background as a **reference point** so the characters, scenarios, and stakes feel relatable — e.g. characters in similar life stages, facing decisions familiar to someone in a startup, managing a family budget, or balancing stable employment with entrepreneurial ambitions. The story should serve the lesson content first; the background just makes it land closer to home.

Use the **Write tool** (not Bash) to create the lesson markdown. Read `.claude/skills/lesson-create-youtube/lesson_template.md` for the full structure with examples.

### Phase 5: Display summary

After saving both files, display:

```
Metadata saved: data/metadata/{channel_slug}/{filename}.json
Lesson saved:   data/lesson/{channel_slug}/{filename}.md

Title:     {video title}
Channel:   {channel name}
Published: {published date}
Duration:  {duration}
```

## Naming Convention

Files are saved under a **channel subdirectory**:
- Lesson: `data/lesson/{channel_slug}/{yymmdd}_{slug}.md`
- Metadata: `data/metadata/{channel_slug}/{yymmdd}_{slug}.json`

Where:
- `{channel_slug}` — channel name: lowercased, spaces replaced with `_`, special characters removed (e.g. `south_china_morning_post`, `themitmonk`, `y_combinator`)
- `{yymmdd}` — from the video published date (e.g. `260227` for 2026-02-27)
- `{slug}` — from the video title: lowercased, spaces replaced with `_`, special characters removed (apostrophes, quotes, colons, question marks), max 50 chars, no trailing underscores

### Example

Channel: "South China Morning Post"
Title: "Why are Hong Kong's fresh graduates struggling to find a job?"
Published: 2026-02-27

→ `data/lesson/south_china_morning_post/260227_why_are_hong_kongs_fresh_graduates_struggling.md`
→ `data/metadata/south_china_morning_post/260227_why_are_hong_kongs_fresh_graduates_struggling.json`

## Rules

1. Use the **transcript** as the primary source of content — it has the full detail
2. Use the **description** for metadata, links, and chapter structure
3. Group all key points into **at most 3 major sections** by theme — rearrange transcript order as needed so related ideas sit together
4. Each section: bullet points (~100 words) + ASCII diagram at the end
5. **Full coverage** — every key point from the transcript must appear. Re-read the transcript after drafting to verify nothing is missing
6. ASCII diagrams should be properly aligned, visually clean, and under ~25 lines each
7. Separate sections with `---` horizontal rules
8. The transcript field in the JSON should contain the full unabridged transcript
9. Always `mkdir -p data/metadata/{channel_slug} data/lesson/{channel_slug}` before writing files
10. Use Python via Bash for JSON operations to avoid shell escaping issues with quotes and special characters
