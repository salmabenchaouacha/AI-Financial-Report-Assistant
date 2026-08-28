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

  return res.data;
};

export const indexDocument = async (documentId) => {
  const res = await axios.post(`${API_BASE}/upload/index/${documentId}`);
  return res.data;
};

export const listDocuments = async () => {
  const res = await axios.get(`${API_BASE}/upload/documents`);
  return res.data;
};

export const listConversations = async () => {
  const res = await axios.get(`${API_BASE}/upload/conversations`);
  return res.data;
};

export const getConversation = async (conversationId) => {
  const res = await axios.get(`${API_BASE}/upload/conversations/${conversationId}`);
  return res.data;
};

export const deleteConversation = async (conversationId) => {
  const res = await axios.delete(`${API_BASE}/upload/conversations/${conversationId}`);
  return res.data;
};

export const askQuestion = async (documentIds, question, conversationId = null) => {
  const res = await axios.post(`${API_BASE}/upload/chat`, {
    document_ids: documentIds,
    question,
    conversation_id: conversationId,
  });
  return res.data;
};

export const generateChart = async (documentIds, question, conversationId = null) => {
  const res = await axios.post(`${API_BASE}/upload/chart`, {
    document_ids: documentIds,
    question,
    conversation_id: conversationId,
  });
  return res.data;
};

export const getStats = async () => {
  const res = await axios.get(`${API_BASE}/upload/stats`);
  return res.data;
};
export const listReports = async () => {
  const res = await axios.get(`${API_BASE}/upload/reports`);
  return res.data;
};


export const saveToReport = async (messageId) => {
  const res = await axios.post(`${API_BASE}/upload/reports/${messageId}/save`);
  return res.data;
};

export const removeFromReport = async (messageId) => {
  const res = await axios.delete(`${API_BASE}/upload/reports/${messageId}/save`);
  return res.data;
};

export const chatWithUpload = async (file, question, conversationId) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("question", question);
  if (conversationId) formData.append("conversation_id", conversationId);

  const res = await axios.post(`${API_BASE}/upload/chat-with-upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};