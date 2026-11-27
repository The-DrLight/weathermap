import ThemeToggle from "./ThemeToggle";

function formatCoordinate(value, positiveLabel, negativeLabel) {
  const hemisphere = value >= 0 ? positiveLabel : negativeLabel;
  return `${Math.abs(value).toFixed(4)}°${hemisphere}`;
}

export default function SystemStatusBar({ error, coords, locationStatus, theme, onToggleTheme }) {
  const isHealthy = !error;
  const placeLabel = locationStatus === "denied" ? "Lagos, Nigeria (default)" : "Current location";
  const coordLabel = coords
    ? `${formatCoordinate(coords.lat, "N", "S")}, ${formatCoordinate(coords.lon, "E", "W")}`
    : "Resolving location…";

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface/90 pt-[env(safe-area-inset-top)] backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-accent">{placeLabel}</p>
          <p className="truncate text-xs text-subtle">{coordLabel}</p>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium sm:text-sm ${
              isHealthy ? "bg-accent-soft text-accent" : "bg-danger-soft text-danger"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${isHealthy ? "bg-accent-strong" : "bg-danger"}`}
              aria-hidden="true"
            />
            {isHealthy ? "API Healthy" : "API Error"}
          </span>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </header>
  );
}
