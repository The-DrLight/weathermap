const MODES = [
  { value: "live", label: "Live Data" },
  { value: "manual", label: "Manual Input" },
];

export default function ModeToggle({ mode, onChange }) {
  return (
    <div className="inline-flex rounded-lg border border-navy-700 bg-navy-900/60 p-1 text-sm">
      {MODES.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          aria-pressed={mode === value}
          className={`rounded-md px-3 py-1.5 font-medium transition ${
            mode === value ? "bg-teal-500 text-navy-950" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
