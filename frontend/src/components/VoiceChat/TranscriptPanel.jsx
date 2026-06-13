import { useEffect, useRef } from "react";

// Scrolling transcript of the voice conversation. `turns` is an array of
// { role: "user" | "assistant", text } committed bubbles. `liveUser` and
// `liveBot` are the in-progress turn's user and assistant text, rendered live
// and growing as transcript deltas stream in (so the reply appears smoothly
// rather than popping in whole at turn end).
export default function TranscriptPanel({ turns, liveUser, liveBot }) {
  const endRef = useRef(null);

  useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [turns, liveUser, liveBot]);

  const empty = turns.length === 0 && !liveUser && !liveBot;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {empty && (
          <p className="mt-10 text-center text-sm text-slate-400">
            Press the mic and ask about anything in your notes.
          </p>
        )}
        {turns.map((turn, i) => (
          <div
            key={i}
            className={`flex ${turn.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
                turn.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {turn.text}
            </div>
          </div>
        ))}
        {liveUser && (
          <div className="flex justify-end">
            <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl bg-indigo-600 px-4 py-2 text-sm text-white">
              {liveUser}
            </div>
          </div>
        )}
        {liveBot && (
          <div className="flex justify-start">
            <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl bg-slate-100 px-4 py-2 text-sm text-slate-800">
              {liveBot}
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
