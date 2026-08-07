import { useState } from "react";
import { useWeatherData } from "./hooks/useWeatherData";
import { postPrediction } from "./services/api";
import { nowInLagos } from "./utils/lagosTime";
import SystemStatusBar from "./components/SystemStatusBar";
import ModeToggle from "./components/ModeToggle";
import LiveReadings from "./components/LiveReadings";
import ManualInputForm from "./components/ManualInputForm";
import PredictionCard from "./components/PredictionCard";
import ValidationPanel from "./components/ValidationPanel";
import NasaComparisonPanel from "./components/NasaComparisonPanel";

const DEFAULT_MANUAL_VALUES = {
  temperature_2m: 27,
  relative_humidity_2m: 80,
  surface_pressure: 1013,
  wind_speed_10m: 8,
  wind_direction_10m: 200,
  cloud_cover: 50,
};

export default function App() {
  const {
    weather,
    prediction,
    validation,
    loading,
    error,
    coords,
    locationStatus,
    locationNotice,
  } = useWeatherData();
  const [mode, setMode] = useState("live");
  const [manualPrediction, setManualPrediction] = useState(null);
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualError, setManualError] = useState(null);

  const handleModeChange = (newMode) => {
    console.log("[App] mode changed", { from: mode, to: newMode });
    setMode(newMode);
  };

  const handleManualSubmit = async (values) => {
    console.log("[App] manual prediction submitted", values);
    setManualSubmitting(true);
    setManualError(null);
    try {
      const result = await postPrediction({ ...values, time: nowInLagos() });
      setManualPrediction(result);
      console.log("[App] manual prediction succeeded", result);
    } catch (err) {
      console.error("[App] manual prediction failed", err);
      setManualError(err);
    } finally {
      setManualSubmitting(false);
    }
  };

  const initialManualValues = weather?.current
    ? {
        temperature_2m: weather.current.temperature_2m,
        relative_humidity_2m: weather.current.relative_humidity_2m,
        surface_pressure: weather.current.surface_pressure,
        wind_speed_10m: weather.current.wind_speed_10m,
        wind_direction_10m: weather.current.wind_direction_10m,
        cloud_cover: weather.current.cloud_cover,
      }
    : DEFAULT_MANUAL_VALUES;

  const displayedPrediction = mode === "live" ? prediction : manualPrediction;
  const displayedError = mode === "live" ? error : manualError;
  const displayedLoading = mode === "live" ? loading : manualSubmitting;

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100">
      <SystemStatusBar weather={weather} error={error} coords={coords} locationStatus={locationStatus} />

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-50 sm:text-3xl">
              Lagos Smart Weather Prediction System
            </h1>
            <p className="mt-1 text-sm text-slate-400">EEG 323: Instrumentation and Measurement II</p>
          </div>
          <ModeToggle mode={mode} onChange={handleModeChange} />
        </header>

        {locationStatus === "requesting" && (
          <div className="rounded-xl border border-navy-700 bg-navy-900/60 px-4 py-3 text-sm text-slate-300">
            Requesting location access...
          </div>
        )}

        {locationNotice && (
          <div className="rounded-xl border border-amber-700/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-300">
            {locationNotice}
          </div>
        )}

        <LiveReadings current={weather?.current} loading={loading} />

        {mode === "manual" && (
          <ManualInputForm
            initialValues={initialManualValues}
            onSubmit={handleManualSubmit}
            submitting={manualSubmitting}
          />
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PredictionCard
            prediction={displayedPrediction}
            loading={displayedLoading}
            error={displayedError}
            source={mode === "live" ? "Live API Data" : "Manual Input"}
            emptyMessage={
              mode === "manual" ? "Submit the form above to run a prediction." : undefined
            }
          />
          <ValidationPanel validation={validation} loading={loading} />
        </div>

        <NasaComparisonPanel coords={coords} />
      </main>
    </div>
  );
}
