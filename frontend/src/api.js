import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

export const getSummary = () => api.get("/anomaly_detections/summary").then(r => r.data);
export const getDetections = (linkId, limit = 50) =>
  api.get("/anomaly_detections", { params: { link_id: linkId, limit } }).then(r => r.data);
export const getReadings = (linkId, limit = 300) =>
  api.get("/link_readings", { params: { link_id: linkId, limit } }).then(r => r.data);