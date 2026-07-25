import { useEffect, useState } from "react";
import { getNasaComparison } from "../services/api";

export default function NasaComparisonPanel({ coords }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!coords) return;

    let cancelled = false;

    getNasaComparison(coords)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [coords]);

  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-slate-100">
        Historical Accuracy Validation (NASA POWER Reference)
      </h2>
      <p className="mt-1 text-xs text-slate-500">
        NASA data is used as a reference standard only and does not influence predictions.
      </p>

      {loading && <p className="mt-4 text-sm text-slate-400">Loading NASA comparison…</p>}

      {!loading && error && (
        <p className="mt-4 text-sm text-red-400/80">
          {error.response?.data?.detail || "Could not reach the NASA comparison service."}
        </p>
      )}

      {!loading && !error && data && (
        <>
          {data.accuracy !== null && (
            <p className="mt-3 text-sm text-slate-300">
              7-day agreement with NASA POWER:{" "}
              <span className="font-semibold text-teal-400">{Math.round(data.accuracy * 100)}%</span>
            </p>
          )}

          {data.days.length === 0 ? (
            <p className="mt-3 text-sm text-slate-400">No comparable days available yet.</p>
          ) : (
            <div className="mt-3 overflow-x-auto rounded-lg border border-navy-700">
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead>
                  <tr className="bg-navy-950/60 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Our Prediction</th>
                    <th className="px-3 py-2 text-right">Confidence</th>
                    <th className="px-3 py-2 text-right">NASA Precip. (mm)</th>
                    <th className="px-3 py-2 text-center">Match</th>
                  </tr>
                </thead>
                <tbody>
                  {data.days.map((row) => (
                    <tr key={row.date} className="odd:bg-navy-900/40 even:bg-navy-950/40">
                      <td className="px-3 py-2 text-slate-300">{row.date}</td>
                      <td className="px-3 py-2 text-slate-200">{row.our_prediction}</td>
                      <td className="px-3 py-2 text-right font-mono text-slate-300">
                        {Math.round(row.confidence * 100)}%
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-slate-300">
                        {row.nasa_precipitation_mm}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {row.correct ? (
                          <span className="text-teal-400">✓</span>
                        ) : (
                          <span className="text-red-400">✗</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}
