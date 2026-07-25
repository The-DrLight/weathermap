import { useWeatherData } from "./hooks/useWeatherData";
import SystemStatusBar from "./components/SystemStatusBar";
import LiveReadings from "./components/LiveReadings";
import PredictionCard from "./components/PredictionCard";
import ValidationPanel from "./components/ValidationPanel";

export default function App() {
  const { weather, prediction, validation, loading, error } = useWeatherData();

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100">
      <SystemStatusBar weather={weather} error={error} />

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        <header>
          <h1 className="text-2xl font-bold text-slate-50 sm:text-3xl">
            Lagos Smart Weather Prediction System
          </h1>
          <p className="mt-1 text-sm text-slate-400">EEG 323 — Instrumentation and Measurement II</p>
        </header>

        <LiveReadings current={weather?.current} loading={loading} />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PredictionCard prediction={prediction} loading={loading} error={error} />
          <ValidationPanel validation={validation} loading={loading} />
        </div>
      </main>
    </div>
  );
}
