/** Shared card shell so every panel has the same padding, border, radius and header. */
export default function Card({ title, subtitle, action, className = "", children }) {
  return (
    <section
      className={`flex min-w-0 flex-col rounded-2xl border border-line bg-surface p-4 shadow-card sm:p-5 lg:p-6 ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-x-3 gap-y-2">
          <div className="min-w-0">
            {title && <h2 className="text-base font-semibold text-fg sm:text-lg">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-subtle">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const CHIP_TONES = {
  neutral: "bg-inset text-muted",
  accent: "bg-accent-soft text-accent",
};

export function Chip({ tone = "neutral", children }) {
  return (
    <span
      className={`inline-flex max-w-full items-center rounded-full px-2.5 py-1 text-xs font-medium ${CHIP_TONES[tone]}`}
    >
      {children}
    </span>
  );
}
