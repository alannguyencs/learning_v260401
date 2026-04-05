# Fetch Video Metadata & Transcript

## Step 1: Fetch video metadata

Fetch the YouTube page HTML and save to a temp file:

```bash
curl -s "https://www.youtube.com/watch?v={VIDEO_ID}" -o /tmp/yt_page.html
```

Then extract metadata using Python regex on the HTML. The most reliable fields come from the embedded JSON (`ytInitialPlayerResponse`), not meta tags.

### Extraction patterns (in order of reliability)

| Field | Primary regex | Fallback |
|-------|--------------|----------|
| title | `<meta name="title" content="([^"]+)"` | `<title>` tag |
| channel | `"ownerChannelName":"([^"]+)"` | `<link itemprop="name" content="...">` |
| channel_url | `"channelId":"([^"]+)"` → build URL | `<meta property="og:url"` |
| published_date | `"publishDate":"([^"]+)"` | `<meta itemprop="datePublished"` |
| duration | `"lengthSeconds":"(\d+)"` → convert to `MM:SS` | `<meta itemprop="duration"` |
| description | `"shortDescription":"((?:[^"\\\\]|\\\\.)*)"` → unicode_escape decode | `<meta property="og:description"` |

### Recommended extraction script

Run as a single Python script via Bash to extract all fields at once:

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

# Channel URL
m = re.search(r'\"channelId\":\"([^\"]+)\"', html)
channel_url = f'https://www.youtube.com/channel/{m.group(1)}' if m else ''

# Published date
m = re.search(r'\"publishDate\":\"([^\"]+)\"', html)
pub_date = m.group(1)[:10] if m else ''

# Duration (convert lengthSeconds to MM:SS)
m = re.search(r'\"lengthSeconds\":\"(\d+)\"', html)
if m:
    secs = int(m.group(1))
    mins, s = divmod(secs, 60)
    duration = f'{mins}:{s:02d}'
else:
    duration = ''

# Description (needs unicode_escape for special chars)
m = re.search(r'\"shortDescription\":\"((?:[^\"\\\\\\\\]|\\\\\\\\.)*)\"', html)
desc = m.group(1).encode().decode('unicode_escape') if m else ''

print(json.dumps({
    'title': title,
    'channel': channel,
    'channel_url': channel_url,
    'published_date': pub_date,
    'duration': duration,
    'description': desc
}, indent=2))
"
```

### Important notes

- Always use `errors='replace'` when reading the HTML — YouTube pages may contain non-UTF8 bytes
- The `shortDescription` regex uses a non-greedy escaped-string pattern to handle `\"` inside the description
- Description may contain unicode escapes like `\u2019` — the `.encode().decode('unicode_escape')` handles this
- Run the page fetch and transcript fetch **in parallel** (separate Bash calls) to save time

## Step 2: Fetch the transcript

Use the `youtube_transcript_api` Python library (v3+):

```python
python3 -c "
from youtube_transcript_api import YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.fetch('{VIDEO_ID}')
for entry in transcript:
    print(entry.text)
" > /tmp/yt_transcript.txt
```

This returns plain text with line breaks saved to a temp file for later embedding in the JSON.

### Fallbacks if transcript fetch fails

1. Try specifying languages: `ytt_api.fetch('{VIDEO_ID}', languages=['en', 'es', 'zh-Hant'])`
3. **Audio transcription fallback** — if the video has no captions at all (error: "Subtitles are disabled"), use `yt-dlp` + `mlx-whisper` to transcribe from audio:

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

**Note:** mlx-whisper may produce hallucinated repetitive text at the end, or when the audio switches between languages (e.g. English narration with Japanese/Chinese interviews). Trim any obviously repeated trailing text before using the transcript.

4. If no transcript available by any method, note this in the metadata and generate the lesson from the description only

## Step 3: Parallel execution

Fetch the page and transcript in **parallel** (two separate Bash tool calls in the same message):

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

Then run the Python extraction script on the saved HTML.
