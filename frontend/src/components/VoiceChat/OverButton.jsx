import { useEffect } from "react";
import { useOverSession } from "../../hooks/useOverSession";
import MicButtonShell from "./MicButtonShell";

// Press-to-talk button for the voice tutor. One 🎙 toggles the *turn*:
// idle/between → start a turn, recording → finish it, speaking → interrupt the
// reply. A separate "End session" control closes the whole session. `onState`
// (optional, stable) is called with the session state on every change.
export default function OverButton({ voice, onEvent, onError, onState }) {
  const { state, error, startTurn, endTurn, interrupt, stop } = useOverSession({
    voice,
    onEvent,
    onError,
  });

  useEffect(() => {
    if (onState) onState(state);
  }, [state, onState]);

  const denied = state === "denied";
  const errored = state === "error";
  const connecting = state === "connecting" || state === "stopping";
  const recording = state === "recording";
  const speaking = state === "speaking";
  const between = state === "between";
  const sessionOpen = recording || speaking || connecting || between;

  const handlePress = () => {
    if (denied || connecting) return undefined;
    if (recording) return endTurn();
    if (speaking) return interrupt();
    return startTurn(); // idle / between / after error
  };

  const tone = denied
    ? "denied"
    : recording
      ? "active"
      : speaking
        ? "speaking"
        : connecting
          ? "connecting"
          : "idle";

  const hint = denied
    ? "Mic permission blocked — grant access in your browser settings."
    : errored
      ? `Voice error: ${error || "unknown"}`
      : connecting
        ? state === "connecting"
          ? "Connecting…"
          : "Ending…"
        : recording
          ? "Recording — press again when you're done."
          : speaking
            ? "Assistant is replying — press to interrupt."
            : "Press to start your turn.";

  const ariaLabel = recording
    ? "Finish turn"
    : speaking
      ? "Interrupt assistant"
      : "Start a turn";

  return (
    <MicButtonShell
      tone={tone}
      hint={hint}
      hintTone={denied || errored ? "error" : "muted"}
      disabled={denied || connecting}
      ariaLabel={ariaLabel}
      buttonProps={{ onClick: handlePress }}
    >
      {sessionOpen && (
        <button
          type="button"
          onClick={stop}
          aria-label="End session"
          className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
        >
          End session
        </button>
      )}
    </MicButtonShell>
  );
}
