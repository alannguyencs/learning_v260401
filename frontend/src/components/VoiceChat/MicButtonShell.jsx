// MicButtonShell — shared visual shell for the voice mic button. Owns the
// circular 🎙 button, the colour / pulse tone states, and the hint row. It
// carries no session logic — the consuming composite maps its hook state onto
// `tone` / `hint` and supplies handlers via `buttonProps`.

const TONE_CLASSES = {
  idle: "bg-indigo-600 hover:bg-indigo-500 ring-1 ring-indigo-400/50",
  connecting: "bg-indigo-500 ring-2 ring-indigo-300 animate-pulse",
  active: "bg-red-600 animate-pulse ring-2 ring-red-400",
  speaking: "bg-emerald-600 ring-2 ring-emerald-300",
  denied: "bg-slate-400 opacity-60 cursor-not-allowed",
};

export default function MicButtonShell({
  tone = "idle",
  hint = "",
  hintTone = "muted",
  disabled = false,
  ariaLabel = "Microphone",
  buttonProps = {},
  children = null,
}) {
  const btnClasses = TONE_CLASSES[tone] ?? TONE_CLASSES.idle;
  const hintColor = hintTone === "error" ? "text-red-600" : "text-slate-500";

  return (
    <div className="border-t border-slate-200 bg-white p-3">
      <div className="mx-auto flex max-w-3xl items-center gap-3">
        <button
          type="button"
          disabled={disabled}
          aria-label={ariaLabel}
          className={`flex h-14 w-14 items-center justify-center rounded-full text-2xl text-white shadow-md transition ${btnClasses}`}
          {...buttonProps}
        >
          🎙
        </button>
        <div className={`flex-1 text-sm ${hintColor}`}>{hint}</div>
        {children}
      </div>
    </div>
  );
}
