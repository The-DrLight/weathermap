const SENSOR_CARDS = [
  { key: "temperature_2m", label: "Temperature", descriptor: "Temperature Sensor (RTD PT100)", unit: "°C", decimals: 1 },
  { key: "relative_humidity_2m", label: "Relative Humidity", descriptor: "Humidity Sensor (Capacitive HIH-4000)", unit: "%", decimals: 0 },
  { key: "surface_pressure", label: "Atmospheric Pressure", descriptor: "Barometric Pressure Sensor (BMP280)", unit: "hPa", decimals: 1 },
  { key: "wind_speed_10m", label: "Wind Speed", descriptor: "Wind Speed Transducer (Cup Anemometer)", unit: "km/h", decimals: 1 },
  { key: "wind_direction_10m", label: "Wind Direction", descriptor: "Wind Direction Sensor (Potentiometric Wind Vane)", unit: "°", decimals: 0 },
  { key: "dew_point_2m", label: "Dew Point Temperature", descriptor: "Magnus Formula Derivation", unit: "°C", decimals: 1 },
  { key: "cloud_cover", label: "Cloud Cover", descriptor: "Cloud Cover Sensor (Ceilometer)", unit: "%", decimals: 0 },
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
          {SENSOR_CARDS.map(({ key, label, descriptor, unit, decimals }) => (
            <div key={key} className="rounded-xl border border-navy-700 bg-navy-950/60 p-3">
              <p className="text-xs font-medium text-slate-400">{label}</p>
              <p className="text-[10px] text-slate-500">{descriptor}</p>
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
