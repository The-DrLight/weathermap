import { useState } from "react";
import { useWeatherData } from "./hooks/useWeatherData";
import { useTheme } from "./hooks/useTheme";
import { postPrediction } from "./services/api";
import { nowInLagos } from "./utils/lagosTime";
import SystemStatusBar from "./components/SystemStatusBar";
import ModeToggle from "./components/ModeToggle";
import LiveReadings from "./components/LiveReadings";
import ManualInputForm from "./components/ManualInputForm";
import PredictionCard from "./components/PredictionCard";
import ModelInputsCard from "./components/ModelInputsCard";
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
  const { theme, toggleTheme } = useTheme();
  const [mode, setMode] = useState("live");
  const [manualPrediction, setManualPrediction] = useState(null);
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualError, setManualError] = useState(null);

  const handleModeChange = (newMode) => {
    console.log("[App] mode changed", { from: mode, to: newMode });
    setMode(newMode);
  };

  const handleManualSubmit = async (values) => {
    console.log("[App] Manual prediction submitted");
    setManualSubmitting(true);
    setManualError(null);
    try {
      const result = await postPrediction({ ...values, time: nowInLagos() });
      setManualPrediction(result);
      console.log("[App] Manual prediction complete");
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
    <div className="min-h-screen bg-canvas text-fg">
      <SystemStatusBar
        error={error}
        coords={coords}
        locationStatus={locationStatus}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6 sm:py-8">
        <div className="mb-5 flex flex-col gap-4 sm:mb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-fg sm:text-3xl">
              Lagos Smart Weather Prediction System
            </h1>
            <p className="mt-1 text-sm text-subtle">EEG 323: Instrumentation and Measurement II</p>
          </div>
          <ModeToggle mode={mode} onChange={handleModeChange} />
        </div>

        {locationStatus === "requesting" && (
          <div className="mb-4 rounded-xl border border-line bg-surface px-4 py-3 text-sm text-muted sm:mb-6">
            Requesting location access...
          </div>
        )}

        {locationNotice && (
          <div className="mb-4 rounded-xl border border-warn/40 bg-warn-soft px-4 py-3 text-sm text-warn sm:mb-6">
            {locationNotice}
          </div>
        )}

        {mode === "manual" && (
          <ManualInputForm
            initialValues={initialManualValues}
            onSubmit={handleManualSubmit}
            submitting={manualSubmitting}
            className="mb-4 sm:mb-6"
          />
        )}

        {/*
          12-column grid. On phones and tablets everything stacks in reading order, with the
          prediction first because it is the headline answer. From lg up, readings (7 cols)
          and the prediction (5 cols) share the top row and the two reference tables share
          the bottom row.
        */}
        <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-12">
          <PredictionCard
            prediction={displayedPrediction}
            loading={displayedLoading}
            error={displayedError}
            source={mode === "live" ? "Live API Data" : "Manual Input"}
            emptyMessage={
              mode === "manual" ? "Submit the form above to run a prediction." : undefined
            }
            className="lg:col-span-5 lg:col-start-8 lg:row-start-1"
          />
          <LiveReadings
            current={weather?.current}
            loading={loading}
            source={weather?.source}
            className="lg:col-span-7 lg:col-start-1 lg:row-start-1"
          />
          <ModelInputsCard features={displayedPrediction?.features_used} className="lg:col-span-12" />
          <ValidationPanel validation={validation} loading={loading} className="lg:col-span-5" />
          <NasaComparisonPanel coords={coords} className="lg:col-span-7" />
        </div>
      </main>
    </div>
  );
}
