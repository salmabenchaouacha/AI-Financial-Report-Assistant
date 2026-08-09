import axios from "axios";

const API_BASE = "http://localhost:5000/api";

export const checkHealth = async () => {
  const res = await axios.get(`${API_BASE}/health`);
  return res.data;
};

export const uploadPdf = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await axios.post(`${API_BASE}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data; // { document_id, filename, status }
};

export const getUploadStatus = async (documentId) => {
  const res = await axios.get(`${API_BASE}/upload/status/${documentId}`);
  return res.data; // { document_id, status }
};