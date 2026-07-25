import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL });

export const getLiveWeather = () => api.get("/weather/live").then((res) => res.data);
export const getPrediction = () => api.post("/predict").then((res) => res.data);
export const getValidation = () => api.get("/validate").then((res) => res.data);
