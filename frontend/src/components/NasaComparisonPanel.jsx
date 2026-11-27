import { useEffect, useState } from "react";
import { getNasaComparison } from "../services/api";
import Card, { Chip } from "./Card";

export default function NasaComparisonPanel({ coords, className = "" }) {
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

  const agreement = data?.accuracy != null ? Math.round(data.accuracy * 100) : null;

  return (
    <Card
      title="Historical Accuracy Check"
      subtitle="NASA POWER is a reference only and does not influence predictions."
      action={agreement !== null && <Chip tone="accent">7-day agreement {agreement}%</Chip>}
      className={className}
    >
      {loading && <p className="text-sm text-muted">Loading NASA comparison…</p>}

      {!loading && error && (
        <p className="text-sm text-danger">
          {error.response?.data?.detail || "Could not reach the NASA comparison service."}
        </p>
      )}

      {!loading && !error && data && data.days.length === 0 && (
        <p className="text-sm text-muted">No comparable days available yet.</p>
      )}

      {!loading && !error && data && data.days.length > 0 && (
        <>
          {/* Phones: one card per day. Tablets and up: a table. */}
          <ul className="space-y-2 sm:hidden">
            {data.days.map((row) => (
              <li key={row.date} className="flex items-center justify-between gap-3 rounded-xl border border-line bg-inset px-3 py-2.5">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-fg">{row.date}</p>
                  <p className="text-xs text-muted">
                    {row.our_prediction} · {Math.round(row.confidence * 100)}% · NASA {row.nasa_precipitation_mm} mm
                  </p>
                </div>
                <MatchMark correct={row.correct} />
              </li>
            ))}
          </ul>

          <div className="hidden overflow-x-auto rounded-lg border border-line sm:block">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-inset text-xs uppercase tracking-wide text-subtle">
                  <th className="px-3 py-2 font-medium">Date</th>
                  <th className="px-3 py-2 font-medium">Our Prediction</th>
                  <th className="px-3 py-2 text-right font-medium">Confidence</th>
                  <th className="px-3 py-2 text-right font-medium">NASA Precip. (mm)</th>
                  <th className="px-3 py-2 text-center font-medium">Match</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.days.map((row) => (
                  <tr key={row.date}>
                    <td className="whitespace-nowrap px-3 py-2.5 text-muted">{row.date}</td>
                    <td className="px-3 py-2.5 text-fg">{row.our_prediction}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums text-muted">
                      {Math.round(row.confidence * 100)}%
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums text-muted">
                      {row.nasa_precipitation_mm}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <MatchMark correct={row.correct} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  );
}

function MatchMark({ correct }) {
  return correct ? (
    <span className="text-lg font-semibold text-accent" role="img" aria-label="Match">
      ✓
    </span>
  ) : (
    <span className="text-lg font-semibold text-danger" role="img" aria-label="No match">
      ✗
    </span>
  );
}
