import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadCSV = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getDatasetInfo = () => api.get("/dataset-info");

export const getStatistics = () => api.get("/statistics");

export const getSummary = () => api.get("/summary");

export const askQuestion = (question, topK = 5) =>
  api.post("/query", { question, top_k: topK });

export const filterRows = (column, operator, value) =>
  api.post("/filter", { column, operator, value: String(value) });

export const aggregateData = (groupBy, aggColumn, aggFunc) =>
  api.post("/aggregate", { group_by: groupBy, agg_column: aggColumn, agg_func: aggFunc });

export default api;
