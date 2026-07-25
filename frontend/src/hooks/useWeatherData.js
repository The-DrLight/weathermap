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
    try {
      const liveData = await getLiveWeather(activeCoords);
      setWeather(liveData);
      const predictionData = await getPrediction(activeCoords);
      setPrediction(predictionData);
      setError(null);
    } catch (err) {
      setError(err);
    }
  }, []);

  // Resolve device geolocation once on mount, falling back to Lagos on denial or failure.
  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setCoords(LAGOS_COORDS);
      setLocationStatus("denied");
      setLocationNotice(LOCATION_DENIED_NOTICE);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lon: position.coords.longitude });
        setLocationStatus("granted");
      },
      () => {
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

    let cancelled = false;

    (async () => {
      setLoading(true);
      await fetchLiveAndPredict(coords);
      if (!cancelled) setLoading(false);
    })();

    getValidation()
      .then((data) => {
        if (!cancelled) setValidation(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      });

    const intervalId = setInterval(() => fetchLiveAndPredict(coords), POLL_INTERVAL_MS);

    return () => {
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
