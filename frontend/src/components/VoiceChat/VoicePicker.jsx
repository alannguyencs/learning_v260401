// Gemini Live prebuilt voices — must match the backend's VOICE_NAMES set
// (service/voice_over/client.py).
export const VOICES = [
  "Aoede",
  "Charon",
  "Fenrir",
  "Kore",
  "Leda",
  "Orus",
  "Puck",
  "Zephyr",
];

// Voice selector. Disabled while a session is live so the choice can't change
// mid-conversation (it only takes effect when the next session opens).
export default function VoicePicker({ voice, onChange, disabled }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-600">
      Voice
      <select
        value={voice}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm disabled:opacity-50"
      >
        {VOICES.map((v) => (
          <option key={v} value={v}>
            {v}
          </option>
        ))}
      </select>
    </label>
  );
}
