const MODES = [
  { value: "live", label: "Live Data" },
  { value: "manual", label: "Manual Input" },
];

export default function ModeToggle({ mode, onChange }) {
  return (
    <div
      role="group"
      aria-label="Data mode"
      className="grid w-full grid-cols-2 gap-1 rounded-xl border border-line bg-inset p-1 text-sm sm:inline-grid sm:w-auto"
    >
      {MODES.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          aria-pressed={mode === value}
          className={`min-h-10 whitespace-nowrap rounded-lg px-4 py-2 font-medium transition ${
            mode === value
              ? "bg-accent-strong text-on-accent shadow-sm"
              : "text-muted hover:text-fg"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
