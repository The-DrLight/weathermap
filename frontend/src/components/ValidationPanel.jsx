import Card from "./Card";

const METRICS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1_score", label: "F1" },
];

const pct = (value) => `${(value * 100).toFixed(1)}%`;

function ActiveBadge() {
  return (
    <span className="ml-2 rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-semibold text-accent">
      ACTIVE
    </span>
  );
}

export default function ValidationPanel({ validation, loading, className = "" }) {
  if (!validation) {
    return (
      <Card title="Model Validation" className={className}>
        <p className="text-sm text-muted">
          {loading ? "Loading training report…" : "No training report available."}
        </p>
      </Card>
    );
  }

  const results = validation.results ?? [];

  return (
    <Card
      title="Model Validation"
      subtitle={`Trained on ${validation.rows_used?.toLocaleString()} hourly rows · ${validation.years_of_history}y history · scored on the newest 20%`}
      className={className}
    >
      {/* Phones: one card per model. Tablets and up: a compact table. */}
      <ul className="space-y-3 sm:hidden">
        {results.map((r) => {
          const isBest = r.model === validation.best_model;
          return (
            <li
              key={r.model}
              className={`rounded-xl border p-3 ${isBest ? "border-accent/40 bg-accent-soft" : "border-line bg-inset"}`}
            >
              <p className={`mb-2 text-sm font-semibold ${isBest ? "text-accent" : "text-fg"}`}>
                {r.model}
                {isBest && <ActiveBadge />}
              </p>
              <dl className="grid grid-cols-4 gap-2 text-center">
                {METRICS.map(({ key, label }) => (
                  <div key={key}>
                    <dt className="text-[10px] uppercase tracking-wide text-subtle">{label}</dt>
                    <dd className="font-mono text-xs tabular-nums text-fg">{pct(r[key])}</dd>
                  </div>
                ))}
              </dl>
            </li>
          );
        })}
      </ul>

      <div className="hidden overflow-x-auto rounded-lg border border-line sm:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-inset text-xs uppercase tracking-wide text-subtle">
              <th className="px-3 py-2 font-medium">Model</th>
              {METRICS.map(({ key, label }) => (
                <th key={key} className="px-3 py-2 text-right font-medium">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {results.map((r) => {
              const isBest = r.model === validation.best_model;
              return (
                <tr key={r.model} className={isBest ? "bg-accent-soft" : ""}>
                  <td className={`whitespace-nowrap px-3 py-2.5 font-medium ${isBest ? "text-accent" : "text-fg"}`}>
                    {r.model}
                    {isBest && <ActiveBadge />}
                  </td>
                  {METRICS.map(({ key }) => (
                    <td key={key} className="px-3 py-2.5 text-right font-mono tabular-nums text-muted">
                      {pct(r[key])}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
