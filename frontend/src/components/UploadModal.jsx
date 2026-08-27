import { useRef, useState } from "react";
import { X, UploadCloud } from "lucide-react";
import { uploadPdfs, indexDocument } from "../api/client";

export default function UploadModal({ onClose, onDone }) {
  const [rows, setRows] = useState([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const processFiles = async (fileList) => {
    const files = Array.from(fileList).filter((f) => f.type === "application/pdf");
    if (files.length === 0) return;

    setRows(files.map((f) => ({ filename: f.name, step: "uploading" })));

    let uploaded = [];
    try {
      const data = await uploadPdfs(files);
      uploaded = data.uploaded;
      setRows((prev) => prev.map((r) => {
        const match = uploaded.find((u) => u.filename === r.filename);
        return match ? { ...r, step: "indexing", documentId: match.document_id } : { ...r, step: "failed" };
      }));
    } catch {
      setRows((prev) => prev.map((r) => ({ ...r, step: "failed" })));
      return;
    }

    for (const doc of uploaded) {
      try {
        await indexDocument(doc.document_id);
        setRows((prev) => prev.map((r) => (r.filename === doc.filename ? { ...r, step: "ready" } : r)));
      } catch {
        setRows((prev) => prev.map((r) => (r.filename === doc.filename ? { ...r, step: "failed" } : r)));
      }
    }
    onDone?.();
  };

  const STEPS = ["uploading", "indexing", "ready"];

  return (
    <div className="upload-overlay" onClick={onClose}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h3>Upload financial reports</h3>
            <p>Drop your PDF reports here or browse files.</p>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={15} /></button>
        </div>

        <div
          className={`dropzone-v2 ${dragging ? "dragging" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); processFiles(e.dataTransfer.files); }}
        >
          <div className="icon-wrap"><UploadCloud size={18} /></div>
          <strong>Drop your PDF reports here</strong>
          <span>or click to browse files</span>
          <input ref={inputRef} type="file" accept="application/pdf" multiple onChange={(e) => processFiles(e.target.files)} />
        </div>

        {rows.map((r, i) => (
          <div className="upload-file-row" key={i}>
            <div className="upload-file-top"><span>{r.filename}</span></div>
            <div className="upload-steps">
              {STEPS.map((s) => (
                <span
                  key={s}
                  className={`upload-step ${r.step === "failed" ? "failed" : r.step === s ? "active" : STEPS.indexOf(r.step) > STEPS.indexOf(s) || r.step === "ready" && s !== "ready" ? "done" : ""}`}
                >
                  {s === "uploading" ? "Uploading" : s === "indexing" ? "Indexing" : "Ready"}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}