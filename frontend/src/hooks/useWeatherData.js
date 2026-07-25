import { useCallback, useEffect, useState } from "react";
import { getLiveWeather, getPrediction, getValidation } from "../services/api";

const POLL_INTERVAL_MS = 60_000;

export function useWeatherData() {
  const [weather, setWeather] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLiveAndPredict = useCallback(async () => {
    try {
      const liveData = await getLiveWeather();
      setWeather(liveData);
      const predictionData = await getPrediction();
      setPrediction(predictionData);
      setError(null);
    } catch (err) {
      setError(err);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      await fetchLiveAndPredict();
      if (!cancelled) setLoading(false);
    })();

    getValidation()
      .then((data) => {
        if (!cancelled) setValidation(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      });

    const intervalId = setInterval(fetchLiveAndPredict, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [fetchLiveAndPredict]);

  return { weather, prediction, validation, loading, error };
}
