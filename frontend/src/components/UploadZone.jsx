import { useRef, useState } from "react";
import { uploadPdfs, indexDocument } from "../api/client";
import LoadingMessage from "./LoadingMessage";

const INDEX_MESSAGES = [
  "Lecture du texte…",
  "Décorticage des tableaux…",
  "Analyse des graphiques…",
  "Rangement dans le registre…",
];

export default function UploadZone({ onDocumentsIndexed }) {
  const [rows, setRows] = useState([]); // { filename, status: uploading|indexing|ready|error, error }
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const processFiles = async (fileList) => {
    const files = Array.from(fileList).filter((f) => f.type === "application/pdf");
    if (files.length === 0) return;

    setRows(files.map((f) => ({ filename: f.name, status: "uploading" })));

    let uploaded = [];
    try {
      const data = await uploadPdfs(files);
      uploaded = data.uploaded;

      setRows((prev) =>
        prev.map((r) => {
          const match = uploaded.find((u) => u.filename === r.filename);
          const err = data.errors.find((e) => e.startsWith(r.filename));
          if (err) return { ...r, status: "error", error: err };
          if (match) return { ...r, status: "indexing", documentId: match.document_id };
          return r;
        })
      );
    } catch (err) {
      setRows((prev) => prev.map((r) => ({ ...r, status: "error", error: "Échec du dépôt" })));
      return;
    }

    // Indexe chaque document déposé avec succès
    for (const doc of uploaded) {
      try {
        await indexDocument(doc.document_id);
        setRows((prev) =>
          prev.map((r) => (r.filename === doc.filename ? { ...r, status: "ready" } : r))
        );
      } catch {
        setRows((prev) =>
          prev.map((r) =>
            r.filename === doc.filename ? { ...r, status: "error", error: "Échec de l'indexation" } : r
          )
        );
      }
    }

    onDocumentsIndexed?.();
  };

  return (
    <div>
      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          processFiles(e.dataTransfer.files);
        }}
      >
        <div className="dropzone-icon">＋</div>
        <p><strong>Déposez vos rapports PDF</strong><br />ou cliquez pour parcourir</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          onChange={(e) => processFiles(e.target.files)}
        />
      </div>

      {rows.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 12 }}>
          {rows.map((r, i) => (
            <div className="upload-row" key={i}>
              <span className="filename">{r.filename}</span>
              {r.status === "uploading" && <LoadingMessage messages={["Dépôt en cours…"]} />}
              {r.status === "indexing" && <LoadingMessage messages={INDEX_MESSAGES} />}
              {r.status === "ready" && <span className="status-ok">Prêt ✓</span>}
              {r.status === "error" && <span className="status-err">{r.error}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}