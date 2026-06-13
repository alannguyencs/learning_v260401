# Voice Chat (Voice Tutor)

[< Prev: Dashboard](./dashboard.md) | [Parent](./index.md)

**Status:** Done

## Related Docs
- Technical: [technical/voice_chat.md](../technical/voice_chat.md)
- Plan: [plan/260609_v2v_over.md](../plan/260609_v2v_over.md)

## Problem

The app accumulates a growing library of personal study notes on technical
topics, but there is no way to *ask* about them out loud. A learner revising
away from the keyboard — walking, commuting, doing chores — cannot quiz
themselves conversationally or get a spoken explanation grounded in what they
have already studied.

## Solution

A single hands-free **voice-to-voice** chatbot. The user presses a microphone
button to take a turn, speaks a question, and presses again to hand the turn to
the tutor; the tutor answers out loud. It is **press-to-talk** ("over mode"):
the user controls when each turn starts and ends, so it works in noisy places
without the assistant talking over them.

While answering, the tutor can quietly look things up. It searches the user's
own study notes by keyword to ground its answer, and it can recall what was said
earlier in the same conversation so it stays consistent across a long session.
The user can interrupt a reply at any time by pressing the button again
(barge-in), and can pick from a set of assistant voices.

## User Flow

```
User opens the Voice tab (/chat)
  │
  ▼
Picks an assistant voice (optional) and presses the mic
  │
  ▼  [Press to start your turn]
Recording — the user speaks; their words appear live on screen
  │
  ▼  [Press again when done]
Assistant is replying — spoken answer plays back, grounded in the user's notes
  │
  ├── Press during the reply ──► Interrupt (barge-in) → start a fresh turn
  │
  ▼  [Reply finishes]
Between turns — press the mic again to ask the next question
  │
  ▼
[End session] tears everything down and releases the microphone
```

What the user sees and hears:
- One microphone button whose label changes with the situation: *Press to start
  your turn* → *Recording — press again when you're done* → *Assistant is
  replying — press to interrupt*.
- A live transcript of the conversation (their questions and the tutor's
  answers) scrolling on screen.
- A separate **End session** control, shown whenever a session is open.

## Scope

**Included:**
- One press-to-talk voice-to-voice conversation mode.
- Spoken answers grounded in the user's terminology notes (keyword search).
- Recall of earlier turns within the same session.
- Barge-in (interrupt the assistant mid-reply).
- Assistant voice selection.
- A live on-screen transcript of the conversation.

**Not included:**
- A typed/text chat mode, or text-to-speech / speech-to-text-only modes.
- Automatic (hands-free) turn detection — the user always presses to talk.
- Persisting conversations across sessions for later browsing (history is used
  only to keep the current session coherent).
- Showing or pricing token usage.

## Acceptance Criteria

- [ ] A "Voice" tab is reachable from the bottom navigation, opening `/chat`.
- [ ] Pressing the mic starts a turn; the button shows "Recording…".
- [ ] The user's words appear on screen live while they speak.
- [ ] Pressing again hands the turn over and the assistant replies out loud.
- [ ] The spoken answer reflects the user's own notes when the question is about
      a studied term.
- [ ] Referring to something said earlier in the session is answered correctly.
- [ ] Pressing the mic during a reply interrupts it and starts a fresh turn.
- [ ] "End session" stops playback, releases the microphone, and returns to idle.
- [ ] Selecting a different voice changes the assistant's voice on the next turn.
- [ ] Denying microphone permission shows a clear, non-blocking message.

---

[< Prev: Dashboard](./dashboard.md) | [Parent](./index.md)
