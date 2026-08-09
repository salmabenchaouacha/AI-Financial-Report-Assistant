import { useState } from "react";
import { uploadPdf } from "../api/client";

export default function UploadZone({ onDocumentReady }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null); // null | "uploading" | "uploaded" | "error"
  const [documentId, setDocumentId] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus(null);
    setErrorMsg("");
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    setErrorMsg("");

    try {
      const data = await uploadPdf(file);
      setDocumentId(data.document_id);
      setStatus(data.status);

      if (onDocumentReady) onDocumentReady(data.document_id);
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        err.response?.data?.error || "Erreur lors de l'upload du fichier"
      );
    }
  };

  return (
    <div style={{ border: "2px dashed #ccc", padding: "24px", borderRadius: "8px" }}>
      <h3>Importer un rapport financier (PDF)</h3>

      <input type="file" accept="application/pdf" onChange={handleFileChange} />

      <button onClick={handleUpload} disabled={!file || status === "uploading"}>
        {status === "uploading" ? "Envoi en cours..." : "Envoyer"}
      </button>

      {status === "uploaded" && (
        <p style={{ color: "green" }}>
          ✅ Fichier importé avec succès. document_id : <code>{documentId}</code>
        </p>
      )}

      {status === "error" && <p style={{ color: "red" }}>❌ {errorMsg}</p>}
    </div>
  );
}