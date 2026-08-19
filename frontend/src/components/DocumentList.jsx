export default function DocumentList({
  documents,
  selectedIds,
  onToggle,
  onDelete
}) {
  if (documents.length === 0) return null;

  return (
    <div className="doc-list">
      <div className="doc-list-title">
        Dossiers ({documents.length})
      </div>

      {documents.map((doc) => (
        <div
          className={`doc-card ${
            selectedIds.includes(doc.document_id) ? "selected" : ""
          }`}
          key={doc.document_id}
        >
          <label className="doc-card-content">
            <input
              type="checkbox"
              checked={selectedIds.includes(doc.document_id)}
              onChange={() => onToggle(doc.document_id)}
              disabled={doc.status !== "indexed"}
            />

            <div className="doc-card-body">
              <span className="doc-card-name">{doc.filename}</span>
              <span className={`doc-badge ${doc.status}`}>
                {doc.status}
              </span>
            </div>
          </label>

          <button
            className="delete-doc-btn"
            onClick={() => onDelete(doc.document_id)}
            title="Supprimer le document"
          >
            🗑️
          </button>
        </div>
      ))}
    </div>
  );
}