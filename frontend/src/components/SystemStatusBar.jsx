function formatCoordinate(value, positiveLabel, negativeLabel) {
  const hemisphere = value >= 0 ? positiveLabel : negativeLabel;
  return `${Math.abs(value).toFixed(4)}°${hemisphere}`;
}

export default function SystemStatusBar({ weather, error, coords, locationStatus }) {
  const isHealthy = !error;
  const lastUpdated = weather?.current?.time
    ? new Date(weather.current.time).toLocaleString("en-NG", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Not available";

  const placeLabel = locationStatus === "denied" ? "Lagos, Nigeria (default)" : "Current location";
  const coordLabel = coords
    ? `${formatCoordinate(coords.lat, "N", "S")}, ${formatCoordinate(coords.lon, "E", "W")}`
    : "Resolving location";

  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-navy-700 bg-navy-950/95 px-4 py-3 backdrop-blur sm:px-6">
      <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
        <span className="font-semibold text-teal-400">{placeLabel}</span>
        <span className="text-slate-500">{coordLabel}</span>
      </div>

      <div className="flex items-center gap-4 text-xs text-slate-400 sm:text-sm">
        <span>
          Last updated: <span className="text-slate-200">{lastUpdated}</span>
        </span>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${
            isHealthy ? "bg-teal-500/10 text-teal-400" : "bg-red-500/10 text-red-400"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${isHealthy ? "bg-teal-400" : "bg-red-400"}`} />
          {isHealthy ? "API Healthy" : "API Error"}
        </span>
      </div>
    </div>
  );
}
