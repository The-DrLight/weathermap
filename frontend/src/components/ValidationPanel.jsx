export default function ValidationPanel({ validation, loading }) {
  if (!validation) {
    return (
      <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-6">
        <h2 className="mb-2 text-lg font-semibold text-slate-100">Model Validation</h2>
        <p className="text-sm text-slate-400">
          {loading ? "Loading training report…" : "No training report available."}
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-100">Model Validation</h2>
        <span className="text-xs text-slate-500">
          Trained on {validation.rows_used?.toLocaleString()} hourly rows · {validation.years_of_history}y history
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-navy-700">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="bg-navy-950/60 text-xs uppercase tracking-wide text-slate-500">
              <th className="px-3 py-2">Model</th>
              <th className="px-3 py-2 text-right">Accuracy</th>
              <th className="px-3 py-2 text-right">Precision</th>
              <th className="px-3 py-2 text-right">Recall</th>
              <th className="px-3 py-2 text-right">F1</th>
            </tr>
          </thead>
          <tbody>
            {validation.results?.map((r) => {
              const isBest = r.model === validation.best_model;
              return (
                <tr
                  key={r.model}
                  className={isBest ? "bg-teal-500/10" : "odd:bg-navy-900/40 even:bg-navy-950/40"}
                >
                  <td className={`px-3 py-2 font-medium ${isBest ? "text-teal-300" : "text-slate-200"}`}>
                    {r.model}
                    {isBest && (
                      <span className="ml-2 rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] font-semibold text-teal-300">
                        ACTIVE
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{(r.accuracy * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{(r.precision * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{(r.recall * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{(r.f1_score * 100).toFixed(1)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
