import axios from "axios";

const API_BASE = "http://localhost:5000/api";

export const checkHealth = async () => {
  const res = await axios.get(`${API_BASE}/health`);
  return res.data;
};

// Upload de plusieurs fichiers en un seul appel
export const uploadPdfs = async (files) => {
  const formData = new FormData();
  files.forEach((file) => formData.append("file", file));

  const res = await axios.post(`${API_BASE}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data; // { uploaded: [...], errors: [...] }
};

export const indexDocument = async (documentId) => {
  const res = await axios.post(`${API_BASE}/upload/index/${documentId}`);
  return res.data;
};

export const listDocuments = async () => {
  const res = await axios.get(`${API_BASE}/upload/documents`);
  return res.data; // { documents: [...] }
};

export const askQuestion = async (documentIds, question) => {
  const res = await axios.post(`${API_BASE}/upload/chat`, {
    document_ids: documentIds,
    question,
  });
  return res.data;
};

export const generateChart = async (documentIds, question) => {
  const res = await axios.post(`${API_BASE}/upload/chart`, {
    document_ids: documentIds,
    question,
  });
  return res.data;
};