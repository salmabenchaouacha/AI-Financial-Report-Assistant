import { useState } from "react";
import { Search, FileText, CheckCircle2, Clock, XCircle, Sparkles } from "lucide-react";

const STATUS_CONFIG = {
  indexed: { label: "Indexed", className: "badge-indexed", Icon: CheckCircle2 },
  uploaded: { label: "Processing", className: "badge-uploaded", Icon: Clock },
  error: { label: "Failed", className: "badge-error", Icon: XCircle },
};

export default function DocumentsPage({ documents, selectedIds, onToggle, onAnalyze }) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = documents.filter((d) => {
    const matchesQuery = d.filename.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = statusFilter === "all" || d.status === statusFilter;
    return matchesQuery && matchesStatus;
  });

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Documents</h1>
          <p>Manage your uploaded financial reports and select which ones to analyze.</p>
        </div>
        {selectedIds.length > 0 && (
          <button className="btn btn-primary" onClick={onAnalyze}>
            <Sparkles size={16} /> Analyze {selectedIds.length} selected
          </button>
        )}
      </div>

      <div className="section">
        <div className="toolbar">
          <div className="search-input">
            <Search size={15} />
            <input
              placeholder="Search documents…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All statuses</option>
            <option value="indexed">Indexed</option>
            <option value="uploaded">Processing</option>
            <option value="error">Failed</option>
          </select>
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state-v2">
            <div className="icon-wrap"><FileText size={20} /></div>
            <strong>No documents found</strong>
            <span>Try a different search or upload a new report.</span>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 32 }}></th>
                <th>Document</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((doc) => {
                const cfg = STATUS_CONFIG[doc.status] || STATUS_CONFIG.uploaded;
                return (
                  <tr key={doc.document_id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(doc.document_id)}
                        onChange={() => onToggle(doc.document_id)}
                        disabled={doc.status !== "indexed"}
                      />
                    </td>
                    <td>
                      <div className="doc-cell">
                        <div className="doc-icon"><FileText size={15} /></div>
                        <div>
                          <div className="doc-name">{doc.filename}</div>
                          <div className="doc-sub">PDF</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${cfg.className}`}>
                        <cfg.Icon size={12} /> {cfg.label}
                      </span>
                    </td>
                    <td className="doc-sub num">
                      {new Date(doc.created_at).toLocaleDateString("fr-FR")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}