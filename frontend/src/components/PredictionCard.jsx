import Card, { Chip } from "./Card";

const TITLE = "24-Hour Rain Prediction";

export default function PredictionCard({ prediction, loading, error, source, emptyMessage, className = "" }) {
  if (!prediction && loading) {
    return (
      <Card title={TITLE} className={className}>
        <div className="flex-1 animate-pulse space-y-4" aria-hidden="true">
          <div className="h-40 rounded-xl border border-line bg-inset" />
          <div className="h-3 rounded-full bg-inset" />
        </div>
        <p className="sr-only">Loading prediction…</p>
      </Card>
    );
  }

  if (!prediction && error) {
    return (
      <Card title="Prediction Unavailable" className={`border-danger/40 ${className}`}>
        <p className="text-sm text-danger">
          {error.response?.data?.detail || "Could not reach the prediction service."}
        </p>
      </Card>
    );
  }

  if (!prediction) {
    return (
      <Card title={TITLE} className={className}>
        <p className="text-sm text-muted">{emptyMessage || "No prediction yet."}</p>
      </Card>
    );
  }

  const isRain = prediction.will_rain;
  const confidencePct = Math.round(prediction.confidence * 100);
  const usesTrends = "dP_1h" in (prediction.features_used ?? {});

  return (
    <Card
      title={TITLE}
      action={source && <Chip tone="accent">{source}</Chip>}
      className={className}
    >
      {/* Verdict and confidence sit side by side on tablets, stacked on phones and desktop columns. */}
      <div className="grid flex-1 gap-4 sm:grid-cols-2 lg:grid-cols-1">
        <div
          className={`flex flex-col items-center justify-center rounded-xl border p-6 text-center ${
            isRain ? "border-accent/40 bg-accent-soft" : "border-warn/40 bg-warn-soft"
          }`}
        >
          <span className="text-5xl" aria-hidden="true">
            {isRain ? "🌧️" : "☀️"}
          </span>
          <p className={`mt-2 text-2xl font-bold sm:text-3xl ${isRain ? "text-accent" : "text-warn"}`}>
            {prediction.label}
          </p>
        </div>

        <div className="flex flex-col justify-center gap-4">
          <div>
            <div className="mb-1.5 flex items-center justify-between text-sm text-muted">
              <span>Confidence</span>
              <span className="font-semibold tabular-nums text-fg">{confidencePct}%</span>
            </div>
            <div
              className="h-3 w-full overflow-hidden rounded-full bg-inset"
              role="progressbar"
              aria-valuenow={confidencePct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Prediction confidence"
            >
              <div
                className={`h-full rounded-full transition-all ${isRain ? "bg-accent-strong" : "bg-warn"}`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>

          <p className="rounded-lg bg-inset px-3 py-2 text-xs leading-relaxed text-muted">
            {usesTrends
              ? "Uses the last 6 hours of weather trends and recent rainfall."
              : "Snapshot-only mode: no recent hourly history was available, so accuracy is lower."}
          </p>
        </div>
      </div>
    </Card>
  );
}
