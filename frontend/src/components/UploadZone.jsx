import { useState } from "react";
import { uploadPdf, indexDocument } from "../api/client";

export default function UploadZone({ onDocumentReady }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null); // null | "uploading" | "indexing" | "ready" | "error"
  const [documentId, setDocumentId] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus(null);
    setErrorMsg("");
  };

  const handleUpload = async () => {
    if (!file) return;

    setErrorMsg("");

    try {
      // Étape 1 : Upload du fichier
      setStatus("uploading");
      const data = await uploadPdf(file);
      setDocumentId(data.document_id);

      // Étape 2 : Indexation (texte + tableaux + images) — peut prendre du temps
      setStatus("indexing");
      await indexDocument(data.document_id);

      // Étape 3 : Le document est prêt, on peut chatter/générer des graphiques
      setStatus("ready");
      if (onDocumentReady) onDocumentReady(data.document_id);
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        err.response?.data?.error || "Erreur lors de l'import ou de l'indexation du fichier"
      );
    }
  };

  return (
    <div style={{ border: "2px dashed #ccc", padding: "24px", borderRadius: "8px" }}>
      <h3>Importer un rapport financier (PDF)</h3>

      <input type="file" accept="application/pdf" onChange={handleFileChange} />

      <button onClick={handleUpload} disabled={!file || status === "uploading" || status === "indexing"}>
        {status === "uploading" && "Envoi en cours..."}
        {status === "indexing" && "Analyse du document en cours..."}
        {(!status || status === "ready" || status === "error") && "Envoyer"}
      </button>

      {status === "indexing" && (
        <p style={{ color: "#888" }}>
          ⏳ Extraction du texte, des tableaux et des images... cela peut prendre une minute.
        </p>
      )}

      {status === "ready" && (
        <p style={{ color: "green" }}>
          ✅ Document prêt. document_id : <code>{documentId}</code>
        </p>
      )}

      {status === "error" && <p style={{ color: "red" }}>❌ {errorMsg}</p>}
    </div>
  );
}