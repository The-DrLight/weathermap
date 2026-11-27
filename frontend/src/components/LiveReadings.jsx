import Card, { Chip } from "./Card";

const COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
const SOURCE_LABELS = {
  owm: "OpenWeatherMap",
  live: "Open-Meteo",
  archive_fallback: "Open-Meteo archive",
};

const compassPoint = (degrees) => COMPASS[Math.round(degrees / 22.5) % 16];

function formatUpdated(time) {
  if (!time) return null;
  const date = new Date(time);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("en-NG", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Six tiles (wind speed and direction share one) so the grid is always 2x3 or 3x2, never ragged.
const TILES = [
  { key: "temperature_2m", label: "Temperature", descriptor: "RTD PT100", unit: "°C", decimals: 1 },
  { key: "relative_humidity_2m", label: "Humidity", descriptor: "Capacitive HIH-4000", unit: "%", decimals: 0 },
  { key: "surface_pressure", label: "Pressure", descriptor: "Barometric BMP280", unit: "hPa", decimals: 1 },
  { key: "wind", label: "Wind", descriptor: "Cup anemometer + vane", unit: "km/h", decimals: 1 },
  { key: "dew_point_2m", label: "Dew Point", descriptor: "Magnus formula", unit: "°C", decimals: 1 },
  { key: "cloud_cover", label: "Cloud Cover", descriptor: "Ceilometer", unit: "%", decimals: 0 },
];

function WindArrow({ degrees }) {
  // Wind direction is where it blows *from*; the arrow points where it blows *to*.
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-4 w-4 shrink-0 text-accent"
      style={{ transform: `rotate(${degrees + 180}deg)` }}
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 19V5M6 11l6-6 6 6" />
    </svg>
  );
}

function Tile({ label, descriptor, value, unit, extra }) {
  return (
    <div className="flex min-w-0 flex-col justify-between rounded-xl border border-line bg-inset p-3 sm:p-4">
      <div>
        <p className="text-xs font-medium text-muted sm:text-sm">{label}</p>
        <p className="truncate text-[11px] text-subtle">{descriptor}</p>
      </div>
      <div className="mt-3">
        <p className="text-2xl font-semibold tabular-nums text-fg sm:text-3xl">
          {value}
          <span className="ml-1 text-sm font-normal text-muted">{unit}</span>
        </p>
        {extra}
      </div>
    </div>
  );
}

function SkeletonTiles() {
  return (
    <div className="grid flex-1 animate-pulse grid-cols-2 gap-3 sm:grid-cols-3" aria-hidden="true">
      {TILES.map(({ key }) => (
        <div key={key} className="h-28 rounded-xl border border-line bg-inset" />
      ))}
    </div>
  );
}

export default function LiveReadings({ current, loading, source, className = "" }) {
  const updated = formatUpdated(current?.time);
  const sourceLabel = SOURCE_LABELS[source] ?? "Open-Meteo";

  return (
    <Card
      title="Live Sensor Readings"
      subtitle={updated ? `Updated ${updated}` : undefined}
      action={<Chip tone="accent">{sourceLabel}</Chip>}
      className={className}
    >
      {!current && loading && <SkeletonTiles />}
      {!current && !loading && <p className="text-sm text-muted">No live data available.</p>}

      {current && (
        <div className="grid flex-1 grid-cols-2 gap-3 sm:grid-cols-3">
          {TILES.map((tile) => {
            if (tile.key === "wind") {
              const direction = current.wind_direction_10m;
              return (
                <Tile
                  key={tile.key}
                  {...tile}
                  value={current.wind_speed_10m?.toFixed(tile.decimals)}
                  extra={
                    direction != null && (
                      <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
                        <WindArrow degrees={direction} />
                        <span className="tabular-nums">
                          {Math.round(direction)}° {compassPoint(direction)}
                        </span>
                      </p>
                    )
                  }
                />
              );
            }
            return <Tile key={tile.key} {...tile} value={current[tile.key]?.toFixed(tile.decimals)} />;
          })}
        </div>
      )}
    </Card>
  );
}
