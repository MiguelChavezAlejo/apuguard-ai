import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 300000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("apuguard_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;