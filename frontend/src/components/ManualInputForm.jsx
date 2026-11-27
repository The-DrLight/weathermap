import { useState } from "react";
import Card from "./Card";

const FIELDS = [
  { name: "temperature_2m", label: "Temperature", unit: "°C", step: "0.1", min: 0, max: 50 },
  { name: "relative_humidity_2m", label: "Relative Humidity", unit: "%", step: "1", min: 0, max: 100 },
  { name: "surface_pressure", label: "Pressure", unit: "hPa", step: "0.1", min: 900, max: 1100 },
  { name: "wind_speed_10m", label: "Wind Speed", unit: "km/h", step: "0.1", min: 0, max: 150 },
  { name: "wind_direction_10m", label: "Wind Direction", unit: "°", step: "1", min: 0, max: 360 },
  { name: "cloud_cover", label: "Cloud Cover", unit: "%", step: "1", min: 0, max: 100 },
];

export default function ManualInputForm({ initialValues, onSubmit, submitting, className = "" }) {
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
    <Card title="Manual Sensor Input" subtitle="Pre-filled from the last live reading" className={className}>
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4">
          {FIELDS.map(({ name, label, unit, step, min, max }) => (
            <label key={name} className="block min-w-0">
              <span className="mb-1 block truncate text-xs font-medium text-muted">
                {label} <span className="text-subtle">({unit})</span>
              </span>
              <input
                type="number"
                inputMode="decimal"
                step={step}
                min={min}
                max={max}
                value={values[name] ?? ""}
                onChange={handleChange(name)}
                required
                // text-base (16px) stops iOS Safari from zooming the page when a field is focused.
                className="block h-11 w-full rounded-lg border border-line bg-inset px-3 text-base tabular-nums text-fg focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </label>
          ))}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="mt-5 h-11 w-full rounded-lg bg-accent-strong px-6 font-semibold text-on-accent transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {submitting ? "Running Prediction…" : "Run Prediction"}
        </button>
      </form>
    </Card>
  );
}
