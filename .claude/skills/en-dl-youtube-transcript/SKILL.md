---
name: en-dl-youtube-transcript
description: Download a YouTube video's transcript and save it as a markdown file. Use when the user provides a YouTube video URL and wants the transcript saved locally.
argument-hint: "[youtube-video-url]"
allowed-tools: Bash, Read, Write
---

# Download YouTube Transcript

Given a YouTube video URL, fetch its metadata and transcript, and save the transcript as a markdown file.

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
Call 2: python3 -c "
from youtube_transcript_api import YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.fetch('{VIDEO_ID}')
for entry in transcript:
    print(entry.text)
" > /tmp/yt_transcript.txt
```

### Transcript fallbacks (if youtube_transcript_api fails)

1. Try specifying languages: `ytt_api.fetch('{VIDEO_ID}', languages=['en', 'es', 'zh-Hant'])`
2. **Audio transcription fallback** — if the video has no captions at all (error: "Subtitles are disabled"), use `yt-dlp` + `mlx-whisper`:

```bash
# Download audio
yt-dlp -x --audio-format mp3 -o "/tmp/%(id)s.%(ext)s" "https://www.youtube.com/watch?v={VIDEO_ID}"

# Transcribe with mlx-whisper
python3 -c "
import mlx_whisper
result = mlx_whisper.transcribe('/tmp/{VIDEO_ID}.mp3', path_or_hf_repo='mlx-community/whisper-large-v3-turbo')
print(result['text'])
" > /tmp/yt_transcript.txt

# Clean up audio file
rm /tmp/{VIDEO_ID}.mp3
```

**Note:** mlx-whisper may produce hallucinated repetitive text at the end. Trim any obviously repeated trailing text before saving.

4. If no transcript available by any method, inform the user and stop.

### Phase 2: Extract metadata

Run a Python script via Bash to extract fields from the saved HTML:

```python
python3 -c "
import re, json

with open('/tmp/yt_page.html', 'r', errors='replace') as f:
    html = f.read()

# Title
m = re.search(r'<meta name=\"title\" content=\"([^\"]+)\"', html)
title = m.group(1).rstrip('.').strip() if m else ''

# Channel
m = re.search(r'\"ownerChannelName\":\"([^\"]+)\"', html)
channel = m.group(1) if m else ''
if not channel:
    m = re.search(r'<link itemprop=\"name\" content=\"([^\"]+)\"', html)
    channel = m.group(1) if m else ''

# Published date
m = re.search(r'\"publishDate\":\"([^\"]+)\"', html)
pub_date = m.group(1)[:10] if m else ''

print(json.dumps({
    'title': title,
    'channel': channel,
    'published_date': pub_date,
}, indent=2))
"
```

### Phase 3: Save transcript markdown

Use the **Write tool** (not Bash) to create the transcript file at:

```
data/transcript/{channel_slug}/{yymmdd}_{slug}.md
```

Ensure the channel subdirectory exists first: `mkdir -p data/transcript/{channel_slug}`

The markdown file format:

```markdown
# {Video Title}

- **Video:** [{Video Title}](https://www.youtube.com/watch?v={VIDEO_ID})
- **Channel:** {Channel Name}
- **Published:** {YYYY-MM-DD}

---

{full unabridged transcript text}
```

### Phase 4: Display summary

After saving the file, display:

```
Transcript saved: data/transcript/{channel_slug}/{yymmdd}_{slug}.md

Title:     {video title}
Channel:   {channel name}
Published: {published date}
```

## Naming Convention

Files are saved under a **channel subdirectory**:

```
data/transcript/{channel_slug}/{yymmdd}_{slug}.md
```

Where:
- `{channel_slug}` — channel name: lowercased, spaces replaced with `_`, special characters removed (e.g. `south_china_morning_post`, `themitmonk`, `y_combinator`)
- `{yymmdd}` — from the video published date (e.g. `260227` for 2026-02-27)
- `{slug}` — from the video title: lowercased, spaces replaced with `_`, special characters removed (apostrophes, quotes, colons, question marks), max 50 chars, no trailing underscores

### Example

Channel: "South China Morning Post"
Title: "Why are Hong Kong's fresh graduates struggling to find a job?"
Published: 2026-02-27

-> `data/transcript/south_china_morning_post/260227_why_are_hong_kongs_fresh_graduates_struggling.md`

## Rules

1. Always use `errors='replace'` when reading the HTML
2. Always `mkdir -p data/transcript/{channel_slug}` before writing files
3. Use the **Write tool** to create the markdown file
4. Include the full unabridged transcript — do not summarize or truncate
