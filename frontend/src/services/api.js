import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  console.log(`[api] -> ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log(`[api] <- ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`[api] <- error ${error.response?.status ?? ""} ${error.config?.url}`);
    return Promise.reject(error);
  }
);

const coordParams = (coords) => (coords ? { lat: coords.lat, lon: coords.lon } : {});

export const getLiveWeather = (coords) =>
  api.get("/weather/live", { params: coordParams(coords) }).then((res) => res.data);

export const getPrediction = (coords) =>
  api.post("/predict", null, { params: coordParams(coords) }).then((res) => res.data);

export const postPrediction = (payload) => api.post("/predict", payload).then((res) => res.data);

export const getValidation = () => api.get("/validate").then((res) => res.data);

export const getNasaComparison = (coords) =>
  api.get("/nasa/compare", { params: coordParams(coords) }).then((res) => res.data);
