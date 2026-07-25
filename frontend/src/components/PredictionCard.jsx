export default function PredictionCard({ prediction, loading, error }) {
  if (!prediction && loading) {
    return (
      <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-6">
        <p className="text-sm text-slate-400">Loading prediction…</p>
      </section>
    );
  }

  if (!prediction && error) {
    return (
      <section className="rounded-2xl border border-red-900/50 bg-red-950/20 p-6">
        <h2 className="text-lg font-semibold text-red-300">Prediction Unavailable</h2>
        <p className="mt-1 text-sm text-red-400/80">
          {error.response?.data?.detail || "Could not reach the prediction service."}
        </p>
      </section>
    );
  }

  if (!prediction) return null;

  const isRain = prediction.will_rain;
  const confidencePct = Math.round(prediction.confidence * 100);
  const featureEntries = Object.entries(prediction.features_used ?? {});

  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-4 sm:p-6">
      <h2 className="mb-4 text-lg font-semibold text-slate-100">24-Hour Rain Prediction</h2>

      <div
        className={`flex flex-col items-center justify-center rounded-xl border p-6 text-center ${
          isRain ? "border-teal-500/40 bg-teal-500/10" : "border-amber-500/40 bg-amber-500/10"
        }`}
      >
        <span className="text-4xl">{isRain ? "🌧️" : "☀️"}</span>
        <p className={`mt-2 text-2xl font-bold ${isRain ? "text-teal-300" : "text-amber-300"}`}>
          {prediction.label}
        </p>
      </div>

      <div className="mt-5">
        <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
          <span>Confidence</span>
          <span className="font-semibold text-slate-200">{confidencePct}%</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-navy-800">
          <div
            className={`h-full rounded-full transition-all ${isRain ? "bg-teal-400" : "bg-amber-400"}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
      </div>

      <div className="mt-5">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          Model Input Features ({featureEntries.length})
        </p>
        <div className="overflow-hidden rounded-lg border border-navy-700">
          <table className="w-full text-left text-xs">
            <tbody>
              {featureEntries.map(([key, value], i) => (
                <tr key={key} className={i % 2 === 0 ? "bg-navy-950/50" : "bg-navy-900/40"}>
                  <td className="px-3 py-1.5 text-slate-400">{key}</td>
                  <td className="px-3 py-1.5 text-right font-mono text-slate-200">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
