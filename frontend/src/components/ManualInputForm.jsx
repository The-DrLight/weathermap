import { useState } from "react";

const FIELDS = [
  { name: "temperature_2m", label: "Temperature", unit: "°C", step: "0.1", min: 0, max: 50 },
  { name: "relative_humidity_2m", label: "Relative Humidity", unit: "%", step: "1", min: 0, max: 100 },
  { name: "surface_pressure", label: "Atmospheric Pressure", unit: "hPa", step: "0.1", min: 900, max: 1100 },
  { name: "wind_speed_10m", label: "Wind Speed", unit: "km/h", step: "0.1", min: 0, max: 150 },
  { name: "wind_direction_10m", label: "Wind Direction", unit: "°", step: "1", min: 0, max: 360 },
  { name: "cloud_cover", label: "Cloud Cover", unit: "%", step: "1", min: 0, max: 100 },
];

export default function ManualInputForm({ initialValues, onSubmit, submitting }) {
  const [values, setValues] = useState(initialValues);

  const handleChange = (name) => (e) => {
    setValues((prev) => ({ ...prev, [name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, Number(value)])
    );
    onSubmit(payload);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-navy-700 bg-navy-900/60 p-4 sm:p-6"
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Manual Sensor Input</h2>
        <span className="text-xs text-slate-500">Pre-filled from the last live reading</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FIELDS.map(({ name, label, unit, step, min, max }) => (
          <label key={name} className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-slate-400">
              {label} ({unit})
            </span>
            <input
              type="number"
              step={step}
              min={min}
              max={max}
              value={values[name] ?? ""}
              onChange={handleChange(name)}
              required
              className="w-full rounded-lg border border-navy-700 bg-navy-950/60 px-3 py-2 text-slate-100 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </label>
        ))}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="mt-5 w-full rounded-lg bg-teal-500 px-4 py-2.5 font-semibold text-navy-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
      >
        {submitting ? "Running Prediction…" : "Run Prediction"}
      </button>
    </form>
  );
}
