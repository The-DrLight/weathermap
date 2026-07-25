const SENSOR_CARDS = [
  { key: "temperature_2m", label: "Temperature", sensor: "RTD PT100 equivalent", unit: "°C", decimals: 1 },
  { key: "relative_humidity_2m", label: "Humidity", sensor: "Capacitive HIH-4000 equivalent", unit: "%", decimals: 0 },
  { key: "surface_pressure", label: "Pressure", sensor: "BMP280 Barometric equivalent", unit: "hPa", decimals: 1 },
  { key: "wind_speed_10m", label: "Wind Speed", sensor: "Cup Anemometer equivalent", unit: "km/h", decimals: 1 },
  { key: "wind_direction_10m", label: "Wind Direction", sensor: "Wind Vane equivalent", unit: "°", decimals: 0 },
  { key: "dew_point_2m", label: "Dew Point", sensor: "Computed — Magnus formula", unit: "°C", decimals: 1 },
  { key: "cloud_cover", label: "Cloud Cover", sensor: "Ceilometer equivalent", unit: "%", decimals: 0 },
];

export default function LiveReadings({ current, loading }) {
  return (
    <section className="rounded-2xl border border-navy-700 bg-navy-900/60 p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Live Sensor Readings</h2>
        <span className="rounded-full bg-teal-500/10 px-2.5 py-1 text-xs font-medium text-teal-400">
          Source: Open-Meteo
        </span>
      </div>

      {!current && loading && <p className="text-sm text-slate-400">Loading live readings…</p>}
      {!current && !loading && <p className="text-sm text-slate-400">No live data available.</p>}

      {current && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {SENSOR_CARDS.map(({ key, label, sensor, unit, decimals }) => (
            <div key={key} className="rounded-xl border border-navy-700 bg-navy-950/60 p-3">
              <p className="text-xs font-medium text-slate-400">
                {label} <span className="text-slate-500">({sensor})</span>
              </p>
              <p className="mt-1 text-xl font-semibold text-slate-100">
                {current[key]?.toFixed(decimals)}
                <span className="ml-1 text-sm font-normal text-slate-400">{unit}</span>
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
