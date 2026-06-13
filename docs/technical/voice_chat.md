# Voice Chat (Voice Tutor) — Technical Design

[< Prev: Testing Context](./testing_context.md) | [Parent](./index.md)

## Related Docs
- Abstract: [abstract/voice_chat.md](../abstract/voice_chat.md)
- Plan: [plan/260609_v2v_over.md](../plan/260609_v2v_over.md)

## Architecture

A single press-to-talk ("Over Mode") voice-to-voice chat. The browser captures
mic audio and plays back the assistant's audio; a **WebSocket** carries binary
PCM both ways plus JSON control frames. The backend proxies a **Gemini Live**
native-audio session, opening a *fresh session per turn* (lazy open) and serving
two function tools the model can call mid-turn.

```
            FRONTEND (React + Tailwind)
  VoiceChatPage ── OverButton ── useOverSession ──┐
     │  AudioWorklet mic-capture (→16 kHz PCM)    │ binary PCM 16k
     │  AudioWorklet playback   (←24 kHz PCM)     │ + JSON control
     ▼                                            ▼
  WebSocket  /api/voice/v2v-over  (same-origin; dev proxy ws:true)
     │
     ▼  BACKEND (FastAPI, layered)
  api/voice_chat.py        gate (JWT cookie) → run_over_session
     │
  service/voice_over/      per-turn Gemini Live session + two pumps
     │            ├── tools.py → search_notes / get_conversation_history
     │            ▼
  service/notes_search.py (BM25)   crud/crud_voice_conversation.py
     │                                  │
  models/terminology_note.py     models/voice_conversation.py
     │
     ▼
  PostgreSQL (prod) / SQLite (tests)        ↕  Gemini Live API (audio + tools)
```

## Data Model

**`TerminologyNote`** (`terminology_notes`) — Postgres mirror of
`terminologies/notes/*.md` with precomputed BM25 statistics.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `rel_path` | String | unique, indexed (project-root-relative path) |
| `title` | String | not null (first `##` heading) |
| `raw_content` | Text | not null (full markdown, returned as grounding) |
| `terminologies` | JSON | term names from `### Key terminologies` |
| `token_length` | Integer | not null (BM25 length normalization) |
| `term_freq` | JSON | `{token: count}` per-document map |
| `updated_at` | DateTime | server default now(), onupdate now() |

**`VoiceConversationTurn`** (`voice_conversation_turns`) — one completed turn,
the source for the `get_conversation_history` tool.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → `users.username`, not null |
| `session_id` | String | indexed (one WebSocket = one session) |
| `turn_index` | Integer | not null (order within session) |
| `user_text` | Text | not null (input transcript) |
| `bot_text` | Text | not null (output transcript) |
| `created_at` | DateTime | server default now() |

Corpus-level BM25 stats (avg length, document frequency, IDF) are **not** stored
— they are recomputed in Python from all rows at query time, so the table can
never drift from its own statistics.

## Pipeline

```
User presses mic (idle/between)
  │
  ▼
useOverSession opens WebSocket → ws.onopen sends {activity_start}
  │
  ▼
api/voice_chat.py: read access_token cookie → get_current_user_from_token
  │   missing/invalid → close 4401 ; unknown ?voice= → close 4001
  ▼
run_over_session → _run_one_turn
  │
  ▼
_await_turn_start: block (NO Gemini session) until {activity_start}
  │
  ▼
client.aio.live.connect(model, config)  ← fresh per-turn session
  │   replay ActivityStart → send {session_ready}
  ▼
browser arms mic → streams 16 kHz PCM frames (only while turnActive)
  │
  ├── model emits tool_call → handle_tool_call → send_tool_response
  │       search_notes(query)            → BM25 over terminology_notes
  │       get_conversation_history()     → recent_turns(session_id)
  │
  ▼
User presses mic again → {activity_end} → Gemini generates spoken reply
  │
  ▼
_pump_gemini_to_browser: stream 24 kHz PCM + transcripts to browser
  │   on turn_complete → _record_live_turn (write VoiceConversationTurn)
  ▼
{turn_complete} → browser → state "between"; session closed; loop
  │
  └── (barge-in) press during reply → {interrupt} → abort + recycle session
```

## Algorithms

### BM25 note ranking (`service/notes_search.py` + `utils/bm25_core.py`)
- Tokenize query: lowercase, strip markdown links, drop stopwords + 1-char tokens.
- Load the whole corpus (`crud.list_all`) and derive avg doc length + document
  frequency in memory.
- Score each note: Robertson–Spärck-Jones IDF × saturated TF (`k1=1.5`,
  `b=0.75`); return top-k with title + capped `raw_content` as grounding.
- Identical math to `terminologies/index/bm25.py` (a parallel copy, kept in sync)
  — verified to produce identical scores.

### Per-turn lazy session loop (`service/voice_over/__init__.py`)
- Each turn opens its **own** Gemini Live session; between turns no session is
  held open, so the user's reading/thinking time never trips Gemini's idle
  deadline (`APIError 1011`).
- `_await_turn_start` blocks on `{activity_start}` before connecting; the
  consumed frame is replayed to Gemini, then `{session_ready}` tells the browser
  to arm the mic.
- Two pumps race with `asyncio.wait(FIRST_COMPLETED)`; the loop ends on WebSocket
  close, recycles on a turn boundary or barge-in.
- A whole-session `asyncio.wait_for(max_seconds)` cap emits `{end, session_cap}`.

### Browser turn state machine (`hooks/useOverSession.js`)
- States: `idle → connecting → recording → speaking → between` (+ `stopping`,
  `denied`, `error`).
- Mic arms on `{session_ready}`, not on click; frames are sent only while
  `turnActive`; an `awaitingSessionReady` gate drops late audio/transcripts after
  a turn ends. `interrupt` flushes playback and sends `{interrupt}` (not
  `activity_end`, which would not abort generation).

## Backend — API Layer

| Method | Path | Auth | In | Out | Close codes |
|--------|------|------|----|-----|-------------|
| WS | `/api/voice/v2v-over?voice=<name>` | JWT cookie (`access_token`) | binary 16 kHz PCM + JSON control (`activity_start`/`activity_end`/`interrupt`) | binary 24 kHz PCM + JSON control (`session_ready`, `input_transcript`, `output_transcript`, `turn_complete`, `end`, `error`) | 4401 no auth · 4001 bad voice · 1011 error |

## Backend — Service Layer

- **`service/voice_over/`** (package, split to respect the 300-line cap):
  - `client.py` — lazy Gemini Live client, `MODEL`, `VOICE_NAMES`, `DEFAULT_VOICE`.
  - `config.py` — `_over_live_config(voice)`: audio response, manual VAD
    (automatic detection **disabled**), transcription on, `thinking_budget=0`,
    both tool declarations, system instruction.
  - `pumps.py` — `_await_turn_start`, browser→gemini + gemini→browser pumps.
  - `emit.py` — audio/transcript emit helpers + `_record_live_turn`.
  - `tools.py` — `handle_tool_call` dispatch (executor-bounded at 4 s).
  - `__init__.py` — `run_over_session` per-turn loop + session cap.
- **`service/notes_search.py`** — `search_notes(db, query, top_k=3)`.

## Backend — LLM Requests Layer

Gemini Live (`gemini-2.5-flash-native-audio-preview-12-2025`, configurable via
`VOICE_LIVE_MODEL`). Response modality is **AUDIO** (spoken), not text — there is
no structured JSON output. Grounding/memory come from two function tools the
model calls mid-turn; the *tool-response* payloads are the structured contract.

Prompt structure:
```
+----------------------------------------------------------+
|  SYSTEM INSTRUCTION                                       |
|  (service/voice_over/resources/voice_system_instruction.md)|
|  - Spoken tutor persona for the user's study notes       |
|  - "Call search_notes BEFORE answering a term question"  |
|  - "Call get_conversation_history for back-references"   |
+----------------------------------------------------------+
|  TOOLS (function declarations)                           |
|   - search_notes(query: string)                          |
|   - get_conversation_history()  (no params)              |
+----------------------------------------------------------+
|  LIVE INPUT                                               |
|   - 16 kHz mic PCM, bounded by activity_start/activity_end|
+----------------------------------------------------------+
```

`search_notes` tool response:

| Field | Type | Description |
|-------|------|-------------|
| `notes` | list | up to 3 BM25 hits |
| `notes[].title` | string | note title |
| `notes[].rel_path` | string | note path |
| `notes[].content` | string | note markdown (≤ 6000 chars) |

`get_conversation_history` tool response:

| Field | Type | Description |
|-------|------|-------------|
| `history` | list | up to 6 recent exchanges, oldest first |
| `history[].user` | string | the user's earlier utterance |
| `history[].assistant` | string | the tutor's earlier reply |

## Backend — CRUD Layer

- **`crud/crud_terminology_notes.py`** — `list_all`, `get_by_rel_path`, `upsert`,
  `delete_by_rel_path`.
- **`crud/crud_voice_conversation.py`** — `add_turn`, `recent_turns(session_id,
  limit)` (newest-N fetched, reversed to oldest-first).
- Population: `scripts/sync_terminology_notes.py` mirrors the notes folder into
  `terminology_notes` (upsert + prune); DDL in `scripts/sql/012_*.sql` /
  `013_*.sql`.

## Frontend — Pages & Routes

- **`/chat`** → `pages/VoiceChatPage.jsx`, under `ProtectedRoute` /
  `AuthenticatedLayout`. Owns the transcript, voice selection, and session state.
- Reachable from a **Voice** tab in `BottomNavBar`.

## Frontend — Components

- `components/VoiceChat/OverButton.jsx` — one mic button (idle/between →
  `startTurn`, recording → `endTurn`, speaking → `interrupt`) + "End session".
- `components/VoiceChat/MicButtonShell.jsx` — shared button visuals/tones.
- `components/VoiceChat/TranscriptPanel.jsx` — conversation bubbles + live
  interim user bubble.
- `components/VoiceChat/VoicePicker.jsx` — voice dropdown (mirrors `VOICE_NAMES`).

## Frontend — Services & Hooks

- `hooks/useOverSession.js` — the turn state machine; opens the WebSocket, wires
  the worklets, sends control frames, plays back audio.
- `utils/liveTranscriber.js` — Web Speech interim transcripts during recording.
- `services/api.js` — `voiceWsUrl(voice)` builds the same-origin WS URL.
- `public/worklets/mic-capture-worklet.js` (→16 kHz Int16 PCM) and
  `public/worklets/playback-worklet.js` (queued 24 kHz playback, flush on
  barge-in).
- `setupProxy.js` — `ws: true` so dev WebSocket upgrades reach the backend.

## External Integrations

- **Gemini Live API** (`google-genai`). Credential: `GEMINI_API_KEY`. The Live
  session streams bidirectional audio and serves the two function tools.
  Per-turn session teardown bounds idle exposure to Gemini's deadline; tool
  reads are bounded at 4 s so a slow read cannot stall a turn past that deadline.
  Errors surface as a JSON `{error}` frame then a 1011 close.

## Constraints & Edge Cases

- **Native-audio + tools**: the chosen model must honor function calling (it
  recalls history only by calling the tool). Confirm on the pinned version via
  `scripts/smoke_v2v_over.py`; fall back to a half-cascade (separate STT → BM25
  pre-fetch) if a model version regresses.
- **Auth on WS**: the browser sends the `access_token` HttpOnly cookie on the WS
  upgrade; the dev proxy must forward it (`ws: true`).
- **Echo / barge-in**: browser `echoCancellation` + playback flush on
  `interrupt` + the drop-late-frames gate.
- **Portability**: BM25 runs in Python over loaded rows, so the same path works
  on Postgres (prod) and SQLite (tests); no Postgres-specific SQL.
- **Corpus growth**: full-scan BM25 is fine for hundreds of notes; move to
  Postgres FTS behind the same `search_notes` interface only if it reaches
  thousands (breaks SQLite test parity).

## Component Checklist

- [x] Model — `TerminologyNote` (`terminology_notes`) + migration 012
- [x] Model — `VoiceConversationTurn` (`voice_conversation_turns`) + migration 013
- [x] CRUD — `crud_terminology_notes`, `crud_voice_conversation`
- [x] Service — `notes_search` (BM25) + `utils/bm25_core`
- [x] Service — `voice_over/` package (per-turn Live session, two pumps, tools)
- [x] LLM — Gemini Live config with `search_notes` + `get_conversation_history`
- [x] System instruction — `resources/voice_system_instruction.md`
- [x] API — `WS /api/voice/v2v-over` (auth + voice gate)
- [x] Script — `sync_terminology_notes.py` (folder → table)
- [x] Script — `smoke_v2v_over.py` (manual end-to-end gate)
- [x] Frontend — worklets, `useOverSession`, `liveTranscriber`
- [x] Frontend — `OverButton`, `MicButtonShell`, `TranscriptPanel`, `VoicePicker`
- [x] Frontend — `VoiceChatPage`, `/chat` route, Voice nav tab, `ws:true` proxy
- [x] Tests — notes search, conversation CRUD, WS gate + tool routing, `useOverSession`
- [x] Live validation — full spoken turn via `smoke_v2v_over.py` against Gemini
      (model called `search_notes`, answered grounded, turn recorded, reply WAV)

---

[< Prev: Testing Context](./testing_context.md) | [Parent](./index.md)
