import { useCallback, useEffect, useRef, useState } from "react";
import apiService from "../services/api";
import OverButton from "../components/VoiceChat/OverButton";
import TranscriptPanel from "../components/VoiceChat/TranscriptPanel";
import VoicePicker from "../components/VoiceChat/VoicePicker";

// The app's single voice chatbot surface: press-to-talk voice-to-voice over the
// user's terminology notes. Owns the transcript built from the session events
// emitted by OverButton / useOverSession.
export default function VoiceChatPage() {
  const [turns, setTurns] = useState([]);
  // In-progress turn, rendered live as deltas arrive so the assistant reply
  // streams word-by-word (instead of popping in whole at turn_complete).
  const [liveUser, setLiveUser] = useState("");
  const [liveBot, setLiveBot] = useState("");
  const [voice, setVoice] = useState("Kore");
  const [voiceState, setVoiceState] = useState("idle");
  // Mirror of the in-progress turn in a ref so handleEvent stays stable (no
  // re-binding of the WebSocket handlers). Two user transcripts are tracked:
  // `browser` is the Web Speech API live text (approximate, shown as a smooth
  // preview while talking) and `gemini` is Gemini's own input transcription
  // (accurate and complete, arrives as deltas before turn_complete). The final
  // committed bubble prefers `gemini` so the whole utterance is captured, not
  // the browser recognizer's truncated/garbled guess.
  const acc = useRef({ browser: "", gemini: "", bot: "" });

  // Restore the saved conversation on mount so a refresh keeps the transcript.
  useEffect(() => {
    let cancelled = false;
    apiService
      .getVoiceHistory()
      .then((data) => {
        if (!cancelled && data?.turns) setTurns(data.turns);
      })
      .catch(() => {
        /* leave the transcript empty if history can't be loaded */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleEvent = useCallback((msg) => {
    // Commit the in-progress turn to the transcript and reset for the next one.
    // Prefer Gemini's accurate transcript for the user bubble; fall back to the
    // browser live text only if Gemini sent none.
    const finalize = () => {
      const user = acc.current.gemini.trim() || acc.current.browser.trim();
      const bot = acc.current.bot.trim();
      if (user || bot) {
        setTurns((prev) => [
          ...prev,
          ...(user ? [{ role: "user", text: user }] : []),
          ...(bot ? [{ role: "assistant", text: bot }] : []),
        ]);
      }
      acc.current = { browser: "", gemini: "", bot: "" };
      setLiveUser("");
      setLiveBot("");
    };

    switch (msg.type) {
      case "input_transcript_live":
        // Browser interim transcript — full text-so-far, replace. Drives the
        // smooth live preview while the user is still talking, but only until
        // Gemini's accurate transcript starts arriving (at turn end).
        acc.current.browser = msg.text;
        if (!acc.current.gemini) setLiveUser(msg.text);
        break;
      case "input_transcript":
        // Gemini's input transcript — deltas, append. Accurate and complete, so
        // it takes over the preview the moment it arrives (right after the user
        // ends the turn, before the reply) and becomes the committed bubble.
        acc.current.gemini += msg.text;
        setLiveUser(acc.current.gemini);
        break;
      case "output_transcript":
        // Assistant transcript — deltas, append. Drives the streaming bubble.
        acc.current.bot += msg.text;
        setLiveBot(acc.current.bot);
        break;
      case "turn_complete":
      case "turn_reset":
        // turn_complete: assistant finished. turn_reset: user interrupted (the
        // backend aborts without a turn_complete). Either way, keep whatever was
        // said so far and start the next turn with fresh bubbles.
        finalize();
        break;
      default:
        break;
    }
  }, []);

  const sessionActive = !["idle", "denied", "error"].includes(voiceState);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
        <h1 className="text-lg font-semibold text-slate-800">Voice Tutor</h1>
        <VoicePicker
          voice={voice}
          onChange={setVoice}
          disabled={sessionActive}
        />
      </header>

      <TranscriptPanel turns={turns} liveUser={liveUser} liveBot={liveBot} />

      <OverButton voice={voice} onEvent={handleEvent} onState={setVoiceState} />
    </div>
  );
}
