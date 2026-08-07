import { useCallback, useEffect, useState } from "react";
import { getLiveWeather, getPrediction, getValidation } from "../services/api";

const POLL_INTERVAL_MS = 60_000;
const GEOLOCATION_TIMEOUT_MS = 10_000;
const LAGOS_COORDS = { lat: 6.5244, lon: 3.3792 };
const LOCATION_DENIED_NOTICE = "Location access denied. Showing Lagos data.";

export function useWeatherData() {
  const [coords, setCoords] = useState(null);
  const [locationStatus, setLocationStatus] = useState("requesting");
  const [locationNotice, setLocationNotice] = useState(null);

  const [weather, setWeather] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLiveAndPredict = useCallback(async (activeCoords) => {
    console.log("[useWeatherData] Fetching weather and prediction...");
    try {
      const liveData = await getLiveWeather(activeCoords);
      setWeather(liveData);
      const predictionData = await getPrediction(activeCoords);
      setPrediction(predictionData);
      setError(null);
      console.log("[useWeatherData] Weather data fetched successfully");
    } catch (err) {
      console.error("[useWeatherData] Weather fetch failed");
      setError(err);
    }
  }, []);

  // Resolve device geolocation once on mount, falling back to Lagos on denial or failure.
  useEffect(() => {
    console.log("[useWeatherData] Resolving device geolocation...");
    if (!("geolocation" in navigator)) {
      console.warn("[useWeatherData] Geolocation unsupported, falling back to Lagos");
      setCoords(LAGOS_COORDS);
      setLocationStatus("denied");
      setLocationNotice(LOCATION_DENIED_NOTICE);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        console.log("[useWeatherData] Geolocation granted");
        setCoords({ lat: position.coords.latitude, lon: position.coords.longitude });
        setLocationStatus("granted");
      },
      () => {
        console.warn("[useWeatherData] Geolocation denied/failed, falling back to Lagos");
        setCoords(LAGOS_COORDS);
        setLocationStatus("denied");
        setLocationNotice(LOCATION_DENIED_NOTICE);
      },
      { timeout: GEOLOCATION_TIMEOUT_MS }
    );
  }, []);

  // Once coordinates are resolved, fetch live data and poll on that location.
  useEffect(() => {
    if (!coords) return;

    console.log("[useWeatherData] Coordinates resolved, starting fetch + poll cycle");
    let cancelled = false;

    (async () => {
      setLoading(true);
      await fetchLiveAndPredict(coords);
      if (!cancelled) setLoading(false);
    })();

    console.log("[useWeatherData] Fetching validation report...");
    getValidation()
      .then((data) => {
        if (!cancelled) setValidation(data);
        console.log("[useWeatherData] Validation report loaded");
      })
      .catch((err) => {
        console.error("[useWeatherData] Validation report failed");
        if (!cancelled) setError(err);
      });

    const intervalId = setInterval(() => {
      console.log("[useWeatherData] Poll tick");
      fetchLiveAndPredict(coords);
    }, POLL_INTERVAL_MS);

    return () => {
      console.log("[useWeatherData] Cleaning up fetch + poll cycle");
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [coords, fetchLiveAndPredict]);

  return {
    weather,
    prediction,
    validation,
    loading: locationStatus === "requesting" || loading,
    error,
    coords,
    locationStatus,
    locationNotice,
  };
}
