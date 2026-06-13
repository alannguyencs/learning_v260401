// Browser-side live speech-to-text via the Web Speech API.
//
// V2V Over Mode disables Gemini's server-side VAD, and Gemini only emits its
// input transcript when the manual-activity turn closes — so nothing shows on
// screen while the user is still talking. This transcriber fills that gap: it
// runs the browser's own recogniser with interim results, so the user's words
// appear in real time during the turn. `lang` is pinned to en-US so the display
// transcript can't drift to another language on short / accented clips.
//
// `createLiveTranscriber()` returns `null` on browsers without the Web Speech
// API — callers fall back to Gemini's at-turn-end transcript gracefully.

export function createLiveTranscriber({ lang = "en-US" } = {}) {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  let recognition = null;

  return {
    // Start a fresh recognition for one turn. `onText` receives the full
    // transcript-so-far (cumulative, not a delta) on every interim result.
    start(onText) {
      try {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = lang;
        recognition.onresult = (event) => {
          let text = "";
          for (let i = 0; i < event.results.length; i += 1) {
            text += event.results[i][0].transcript;
          }
          if (text) onText(text);
        };
        recognition.start();
      } catch {
        // start() throws if a recognition is already running — ignore.
      }
    },

    stop() {
      try {
        if (recognition) recognition.stop();
      } catch {
        // ignore
      }
      recognition = null;
    },
  };
}
