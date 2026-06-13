# Solution: Voice-to-Voice Tutor over the Terminology Notes

**Status:** Plan

## Related Docs
- Requirements: [requirements.md](./requirements.md)
- Documentation conventions: [documentation_hierarchy.md](./documentation_hierarchy.md)
- Terminology index internals: `terminologies/index/README.md`

---

## 1. What we are building

A single **voice-to-voice "Over Mode" (press-to-talk) chatbot mode** for this
learning app — requirement #3 says "voice to voice **over**", which maps exactly
to the reference projects' **Over Mode** (`/v2v-over`), not the server-VAD
variant. The user **presses a mic button to take a turn**, speaks, presses again
to hand the turn to the model; the app streams the audio to Google **Gemini
Live**; Gemini answers in spoken audio that plays back through the speakers.
While answering, the model can call two backend **tools**:

1. **`search_notes(query)`** — keyword (BM25) retrieval over a new PostgreSQL
   table that mirrors every file in `terminologies/notes/`. This grounds the
   answer in the user's own study notes.
2. **`get_conversation_history(limit)`** — loads the recent turns of the
   current voice conversation so the model can stay coherent across a long
   session.

The model decides per-turn whether it needs grounding or history; latency for a
lookup is paid only on the turns that need it.

This design ports the proven **Over Mode** pipeline from
`/Users/alan/Documents/projects/api_cognitive_health_chatbot` (backend
`service/v2v_over/`) and `/Users/alan/Documents/projects/f42` (frontend
`useOverSession` hook + audio worklets + the `V2VOverButton` interaction), and
swaps their pgvector RAG tool for a **keyword BM25 tool** backed by Postgres —
matching requirement #2 ("keyword based e.g. TF-IDF, bm25") and reusing the BM25
algorithm already living in `terminologies/index/bm25.py`.

> **The two tools are not new to the reference** — its Over Mode already
> registers exactly `search_knowledge_base` **and** `get_conversation_history`,
> because the native-audio Live model recalls earlier turns by *calling* the
> history tool (passive system-prompt injection was not honored). So requirement
> #2's "two tools" maps 1:1 onto a working pattern; we only replace the
> embedding-based KB tool with our BM25 `search_notes` tool.

---

## 2. Why these choices

| Decision | Rationale |
|---|---|
| **Gemini Live native-audio model** for V2V | Both reference projects already use it; it does STT + reasoning + TTS in one bidirectional stream, so there is no separate STT/TTS to stitch. Aligns with the app's existing Gemini-only LLM policy (CLAUDE.md). |
| **WebSocket** transport (binary PCM both ways + JSON control) | Lowest-friction realtime path; proven in `api/core/chat/v2v.py`. No WebRTC infra needed. |
| **BM25, not embeddings**, for note retrieval | Requirement #2 explicitly asks for keyword search. We already have a tuned BM25 implementation (`terminologies/index/bm25.py`) — port its math, don't reinvent. Avoids an embedding API call on the hot path. |
| **Store per-note token stats in Postgres, score in Python** | Keeps the query portable: the same code path runs against Postgres (prod) and SQLite in-memory (tests), honoring the CLAUDE.md gotcha "avoid Postgres-specific SQL in shared queries." Mirrors how `bm25.py` already recomputes IDF on demand so the table can't drift. |
| **Two function-calling tools** (not one RAG blob) | Requirement #2 names exactly two: history + notes. Function-calling lets the model fetch each only when needed — and the reference's Over Mode *already* uses this exact two-tool shape. |
| **One chatbot mode = V2V Over** (press-to-talk) | Requirement #3 ("voice to voice **over**"). We port only Over Mode; we do not port the standard server-VAD V2V or the T2T / T2S / S2T modes from f42. |
| **Per-turn button drives turn boundaries** | Over Mode disables automatic VAD; the user's button click sends `activity_start` / `activity_end` / `interrupt` frames. This is the behavior to copy verbatim from `V2VOverButton` + `useOverSession`. |

---

## 3. End-to-end pipeline

```
                         BROWSER (React + Tailwind)
   ┌───────────────────────────────────────────────────────────────┐
   │  VoiceChatPage  +  OverButton (one mic toggles the TURN)      │
   │   click idle→record:  send {activity_start}                   │
   │   click record→done:  send {activity_end}                     │
   │   click speaking→barge:send {interrupt}                       │
   │   mic ──getUserMedia──► AudioWorklet "mic-capture"            │
   │      (frames sent ONLY while turnActive, 48kHz→16kHz PCM)      │
   │   speaker ◄─ AudioWorklet "playback" ◄─ Int16→Float32          │
   └───────────────┬───────────────────────────────▲───────────────┘
                   │ binary PCM 16kHz               │ binary PCM 24kHz
                   │ + JSON control                 │ + JSON control
                   │ (activity_start/end/interrupt) │ (session_ready,
                   ▼                                │  transcripts, turn_complete)
            WebSocket  /api/voice/v2v-over?voice=Kore │
   ┌───────────────┴────────────────────────────────┴──────────────┐
   │  BACKEND (FastAPI, layered)                                    │
   │                                                                │
   │  api/voice_chat.py   ── auth gate (JWT cookie), accept WS      │
   │        │                                                       │
   │  service/voice_over/ ── run_over_session()  (per-turn loop)   │
   │        │   await {activity_start}  ← LAZY: no Gemini session  │
   │        │   open fresh Gemini Live session for THIS turn       │
   │        │   send {session_ready} → browser arms mic            │
   │        │   run two async pumps until turn_complete/interrupt: │
   │        │     • browser → gemini   (mic frames)                │
   │        │     • gemini  → browser  (audio + transcripts)       │
   │        │   close session, loop back to await next turn        │
   │        │                                                       │
   │        ▼   on tool_call from the model                        │
   │  ┌───────────────────────────────────────────────┐           │
   │  │ search_notes(query)        get_history(limit)  │           │
   │  └─────┬───────────────────────────┬─────────────┘           │
   │        ▼                           ▼                          │
   │  service/notes_search.py    crud/voice_conversation.py       │
   │   (BM25 over rows)           (recent turns for this session)  │
   │        ▼                           ▼                          │
   │  crud/terminology_notes.py   models/voice_conversation.py    │
   │        ▼                                                       │
   │  models/terminology_note.py  ◄── synced from terminologies/notes/ │
   └────────────────────────────────┬──────────────────────────────┘
                                     ▼
                              PostgreSQL (prod) / SQLite (tests)
```

---

## 3a. Button / turn protocol (copy this behavior verbatim)

The Over Mode interaction is driven by **one mic button** plus a separate **"End
session"** control — ported from `f42/.../composites/V2VOverButton.jsx` and
`hooks/useOverSession.js`. The single mic button means a different thing in each
state; the click handler branches on the current state:

| Current state | Button label / hint | Click action | Frame sent | Next state |
|---|---|---|---|---|
| `idle` (no session) | "Press to start your turn." | `startTurn()` → open WS | (on `ws.onopen`) `{activity_start}` | `connecting` |
| `between` (session open, no turn) | "Press to start your turn." | `startTurn()` | `{activity_start}` | `connecting` |
| `connecting` | "Connecting…" | *(disabled)* | — | `recording` on `session_ready` |
| `recording` | "Recording — press again when you're done." | `endTurn()` | `{activity_end}` | `speaking` |
| `speaking` | "Assistant is replying — press to interrupt." | `interrupt()` (flush playback) | `{interrupt}` | `between` |
| `denied` / `error` | mic-blocked / error hint | *(disabled / retry)* | — | — |

**"End session"** (visible whenever a session is open) calls `stop()` → closes
the WebSocket and tears down all audio nodes.

Rules to preserve exactly when porting:

- **Lazy per-turn session.** The mic is **not** armed on click. The button sends
  `activity_start`, the backend opens a *fresh* Gemini Live session for that turn
  and replies `{session_ready}`; only then does the hook arm the mic
  (`beginRecordingTurn`) and start sending frames. This avoids Gemini's idle
  deadline (`code 1011`) while the user reads/thinks between turns.
- **Frames flow only while `turnActive`.** The mic-capture worklet always runs
  (kept alive by a muted gain → destination hop), but `capture.port.onmessage`
  forwards PCM to the socket **only** between `activity_start` and `activity_end`.
- **Barge-in.** `interrupt()` flushes the playback worklet locally, sends
  `{interrupt}` (which aborts the in-progress generation server-side — note
  `activity_end` would *not* stop the model), emits a `turn_reset` UI event so
  the next turn's transcript starts fresh, and returns to `between`.
- **Drop-late-frames gate.** After `turn_complete` / `interrupt`, an
  `awaitingSessionReady` flag discards any stale in-flight audio/transcript
  frames until the next turn's `session_ready` arrives.
- **Browser-side live transcript.** While recording, a Web Speech transcriber
  (`liveTranscriber.js`) emits interim `input_transcript_live` events to fill the
  gap before Gemini's server-side input transcript (which only lands at
  turn close under manual VAD).

Control-frame vocabulary (browser → server): `activity_start`, `activity_end`,
`interrupt`. Server → browser: `session_ready`, `input_transcript`,
`output_transcript`, `turn_complete`, `usage`, `end`, `error`.

---

## 4. Data model (new tables)

Two new SQLAlchemy models, following the existing `models/content.py` style
(integer PK, `server_default=func.now()`, `Text`/`JSON` columns).

### 4.1 `terminology_notes` — the searchable corpus

One row per file in `terminologies/notes/`. Holds both the readable content and
the precomputed BM25 statistics so search needs no re-tokenization at query
time.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `rel_path` | String, unique, indexed | e.g. `terminologies/notes/260604_vllm.md` — the stable key used by the sync script. |
| `title` | String | First `##` heading of the note. |
| `raw_content` | Text | Full markdown body — returned to the model as grounding. |
| `terminologies` | JSON | List of term names parsed from the `### Key terminologies` section (mirrors `notes_terminologies_mapping.json`). |
| `token_length` | Integer | Number of BM25 tokens in the doc (for length normalization). |
| `term_freq` | JSON | `{token: count}` map — exactly the per-document payload `bm25.py` already stores in `notes.json`. |
| `updated_at` | DateTime | `onupdate=func.now()` — lets the sync script skip unchanged files. |

> **Why both `raw_content` and `term_freq`?** `term_freq` drives ranking;
> `raw_content` is what we hand back to the model once a note ranks highly. The
> corpus-level stats BM25 needs (avg doc length, document frequency, IDF) are
> **recomputed in Python from all rows at query time** — same approach as the
> current `bm25.py`, so the table can never go stale relative to its own stats.

### 4.2 `voice_conversation_turns` — V2V history (Tool #1's source)

One row per completed turn, scoped to a user and a voice session.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → users | Whose conversation. |
| `session_id` | String, indexed | One V2V WebSocket connection = one session id (issued at WS accept). |
| `turn_index` | Integer | Ordering within the session. |
| `user_text` | Text | Input transcript (from Gemini `input_transcription`). |
| `bot_text` | Text | Output transcript (from `output_transcription`). |
| `created_at` | DateTime | `server_default=func.now()`. |

Recording mirrors `service/v2v_over/pumps.py::_record_live_turn` in the
reference: on each `turn_complete`, the accumulated input/output transcription
deltas are written as one row (best-effort; transcript-less turns are skipped).
Because Over Mode tears the per-turn Gemini session down after each turn, this
DB row is the **only** thing that survives — the `get_conversation_history` tool
reads it back, which is why history recall must go through the table, not
in-memory session state.

---

## 5. Backend components (layered, per CLAUDE.md)

Dependencies flow `api → service → crud → models` only.

### 5.1 `models/terminology_note.py`, `models/voice_conversation.py`
SQLAlchemy ORM for the two tables above.

### 5.2 `crud/crud_terminology_notes.py`
Pure DB ops, no business rules:
- `list_all(db) -> List[TerminologyNote]` — load the whole corpus (small: 7
  notes today, ~hundreds at scale; full scan is fine and keeps BM25 portable).
- `upsert(db, rel_path, title, raw_content, terminologies, token_length, term_freq)`
- `get_by_rel_path(db, rel_path)`, `delete_by_rel_path(db, rel_path)`

### 5.3 `crud/crud_voice_conversation.py`
- `add_turn(db, user_id, session_id, turn_index, user_text, bot_text)`
- `recent_turns(db, session_id, limit) -> List[...]` — for Tool #1.

### 5.4 `service/notes_search.py` — **the BM25 retrieval brain**
Ports the scoring functions from `terminologies/index/bm25.py` (tokenizer with
markdown-link stripping + stopwords, Robertson–Spärck-Jones IDF, `k1=1.5`,
`b=0.75`). Public API:
```python
def search_notes(db, query: str, top_k: int = 3) -> list[NoteHit]
```
It loads `crud.list_all(db)`, computes corpus stats (avgdl, doc_freq) in
memory, scores each row, and returns the top-k notes with `rel_path`, `title`,
a relevance score, and a trimmed `raw_content` excerpt to feed the model.

> The existing `bm25.py` tokenizer/scorer is the single source of truth for the
> algorithm — extract it into a small shared helper so the file-based CLI and
> the DB-backed service stay identical. (The shared helper can live in
> `service/notes_search.py` and be imported by a thin adapter, or be lifted to
> `backend/src/utils/bm25_core.py`.)

### 5.5 `service/voice_over/` — the Over Mode session (ported)
Split like the reference's `service/v2v_over/` package to respect the 300-line
cap:
- `client.py` — lazy Gemini Live client + `MODEL` constant.
- `config.py` — `_over_live_config(voice)`: `response_modalities=["AUDIO"]`,
  chosen voice, `input/output_audio_transcription` on, `thinking_budget=0`,
  **automatic VAD disabled** (manual turn control), and the **two tool
  declarations** (`search_notes`, `get_conversation_history`).
- `pumps.py` — the two streaming pumps + `_handle_tool_call`, which dispatches
  to `notes_search.search_notes` or `crud_voice_conversation.recent_turns` and
  replies via `session.send_tool_response(...)`. Includes `_await_turn_start`
  (block until `{activity_start}`) and the manual-turn browser pump.
- `__init__.py` — `run_over_session(ws, *, user, voice, session_id, max_seconds)`
  → the **per-turn loop**: await `activity_start` (no session held idle), open a
  fresh Live session, replay `activity_start`, emit `session_ready`, run the two
  pumps until `turn_complete`/`interrupt`, close the session, loop.
- `resources/voice_system_instruction.md` — persona/guardrails (per CLAUDE.md,
  prompts live under `resources/`, not inlined). The persona: a tutor for *this
  user's* notes; instruct it to call `search_notes` before answering any
  question about a technical term, and `get_conversation_history` when the user
  refers back to something said earlier. (The reference confirms the native-audio
  model only recalls past turns when explicitly told to call this tool.)

### 5.6 `api/voice_chat.py` — the WebSocket router (ported)
- `WS /api/voice/v2v-over?voice=<name>`: read JWT from the `access_token` cookie
  (reusing `authenticate_user_from_request` semantics), close `4401` if absent,
  close `4001` if the voice name is unknown, else `accept()` and call
  `run_over_session`. Wrap errors → JSON `{"type":"error"}` then close `1011`.
  Enforce a hard session cap via `asyncio.wait_for`.
- Register in `api/api_router.py` under `/api`.

### 5.7 Sync script — `scripts/sync_terminology_notes.py`
Reads every `terminologies/notes/*.md`, tokenizes with the shared BM25 helper,
parses the `### Key terminologies` section (reuse `mapping.parse_terminology_entries`
logic), and **upserts** into `terminology_notes`; deletes rows whose files are
gone. Run on deploy and after any note edit — analogous to how
`scripts/seed_local_db.py` seeds content. (Exempt from the 300-line cap, like
all of `scripts/`.)

---

## 6. Frontend (single V2V Over mode)

React 18 + react-router-dom v6 + Tailwind + axios (`withCredentials: true`),
matching the existing `frontend/src/` conventions. The audio plumbing and the
**button-driven turn behavior** are ported from f42's Over Mode (see §3a for the
state table to reproduce).

- **`public/worklets/mic-capture-worklet.js`** — port from f42: decimate the
  native capture rate (≈48 kHz) to 16 kHz Int16 PCM in ~100 ms chunks.
- **`public/worklets/playback-worklet.js`** — port from f42: queue Float32
  chunks, drain to output, support **flush on interrupt** (barge-in).
- **`hooks/useOverSession.js`** — port of f42's `useOverSession.js` (NOT
  `useLiveSession.js`): open mic with `echoCancellation/noiseSuppression/
  autoGainControl`, build capture (native rate) + playback (24 kHz)
  `AudioContext`s, wire the worklets, open the WebSocket to `/v2v-over`
  (`binaryType="arraybuffer"`). Exposes `{ state, error, startTurn, endTurn,
  interrupt, stop }`. State machine: `idle | connecting | recording | speaking |
  between | stopping | denied | error`. Preserves the lazy-open / arm-on-
  `session_ready` / drop-late-frames / `turnActive`-gated send rules from §3a.
- **`components/VoiceChat/OverButton.jsx`** — port of f42's `V2VOverButton.jsx`:
  **one mic button** whose click handler branches on `state` (idle/between →
  `startTurn`, recording → `endTurn`, speaking → `interrupt`), plus a separate
  **"End session"** button (calls `stop`) shown whenever a session is open. Tone
  + hint per the §3a table.
- **`components/VoiceChat/`** — a live transcript panel (user + bot bubbles fed
  by `input_transcript_live` / `input_transcript` / `output_transcript`, reset
  on `turn_reset`), and a voice picker. This is the app's only chatbot UI.
- **`primitives/liveTranscriber.js`** — port from f42: Web Speech API interim
  transcripts during recording (`input_transcript_live` events).
- **`pages/VoiceChatPage.jsx`** + a `/chat` route under the existing
  `ProtectedRoute`/`AuthenticatedLayout`.
- **`services/api.js`** — add the WS URL builder here (endpoints are centralized
  in this file per CLAUDE.md), not inline in components.
- `setupProxy.js` already proxies `/api` to the backend; WebSocket upgrade for
  `/api/voice/*` must be allowed through (set `ws: true` on that proxy entry).

---

## 7. Configuration

Add to `.env` / `src/configs.py` (`pydantic-settings`, typed defaults):

| Key | Purpose |
|---|---|
| `GEMINI_API_KEY` | already present — Gemini Live uses the same key. |
| `VOICE_LIVE_MODEL` | e.g. `gemini-2.5-flash-native-audio-preview-12-2025`. |
| `VOICE_SESSION_MAX_SECONDS` | hard cap per WS session (e.g. `900`). |
| `VOICE_DEFAULT_NAME` | default Gemini voice (e.g. `Kore`). |

Dependency: add `google-genai>=1.74.0` to `backend/requirements.txt` (the Live
API client). No new frontend npm deps — audio uses native browser Web Audio.

---

## 8. Testing (SQLite in-memory, per CLAUDE.md)

- **`tests/test_notes_search.py`** — seed a handful of `terminology_notes` rows
  via the test session, assert BM25 ranking (a query matching a note's key term
  ranks it first; empty query returns nothing). Must run through
  `conftest.py`'s SQLite override — the Python-side BM25 makes this trivial
  since there is no Postgres-specific SQL.
- **`tests/test_voice_conversation_crud.py`** — `add_turn` / `recent_turns`
  ordering and `limit`.
- **`tests/test_voice_chat_ws.py`** — auth gate close codes (`4401`/`4001`) with
  Gemini Live mocked; verify a mocked `tool_call` for `search_notes` routes to
  `notes_search` and a `send_tool_response` is issued.
- Frontend: a Jest test for `useVoiceSession` state transitions with WebSocket
  and `AudioContext` mocked.

---

## 9. Build order (phased)

1. **Corpus in Postgres** — models + crud + `sync_terminology_notes.py` + the
   BM25 helper extracted from `bm25.py`; verify `search_notes` returns sane
   rankings against the 7 existing notes. *(Tool #2 ready.)*
2. **Conversation history** — `voice_conversation_turns` model + crud. *(Tool #1
   ready.)*
3. **Over Mode session** — port `service/voice_over/` + `api/voice_chat.py`, wire
   both tools into the Live config, smoke-test the per-turn WS protocol
   (`activity_start` → `session_ready` → audio → `turn_complete`) with a script
   before any UI.
4. **Frontend** — port worklets + `useOverSession` + `OverButton` (the §3a turn
   behavior) + `liveTranscriber`, build `VoiceChatPage`, add the route and proxy
   WS flag.
5. **Docs** — split this into `abstract/voice_chat.md` + `technical/voice_chat.md`
   per the documentation hierarchy, add the pipeline to
   `technical/system_pipelines.md`.

---

## 10. Open questions / risks

- **Native-audio model + function calling**: *largely de-risked* — the
  reference's Over Mode already runs **both** tools through the native-audio Live
  model (it depends on the model calling `get_conversation_history`). Still
  smoke-test in Phase 3 against our pinned model version, and keep the
  half-cascade (separate STT → BM25 pre-fetch → Live answer) as a documented
  fallback if a future model version declines tools.
- **Echo / barge-in**: rely on browser `echoCancellation` + the playback
  worklet's flush on `interrupt()`, plus the `awaitingSessionReady` drop-late-
  frames gate, exactly as in f42's Over Mode.
- **Corpus growth**: full-scan BM25 is fine for hundreds of notes. If the
  corpus reaches thousands, move ranking into Postgres FTS (`tsvector`/`ts_rank`)
  behind the same `service/notes_search.py` interface — but that breaks SQLite
  test parity, so defer until actually needed.
- **Auth on WebSocket**: cookies are sent on WS upgrade by the browser; confirm
  the JWT cookie (`access_token`, `HttpOnly`) reaches the WS handler through the
  dev proxy.

---

[Requirements](./requirements.md) | [Docs index](./abstract/index.md)
