import { useEffect, useState } from "react";
import { Plus, FileText, CheckCircle2, Clock, XCircle } from "lucide-react";
import { getStats } from "../api/client";

const STATUS_CONFIG = {
  indexed: { label: "Indexed", className: "badge-indexed", Icon: CheckCircle2 },
  uploaded: { label: "Processing", className: "badge-uploaded", Icon: Clock },
  error: { label: "Failed", className: "badge-error", Icon: XCircle },
};

export default function OverviewPage({ documents, onNavigate, onUploadClick }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, [documents]);

  const recent = [...documents]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 6);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Financial Intelligence</h1>
          <p>Analyze financial reports, extract insights and generate data-driven visualizations.</p>
        </div>
        <button className="btn btn-primary" onClick={onUploadClick}>
          <Plus size={16} /> Upload document
        </button>
      </div>

      <div className="kpi-grid">
        <KpiCard label="Documents" value={stats?.documents ?? "—"} />
        <KpiCard label="Indexed" value={stats?.indexed_documents ?? "—"} />
        <KpiCard label="Analyses" value={stats?.analyses ?? "—"} />
        <KpiCard label="Charts" value={stats?.charts ?? "—"} />
      </div>

      <div className="section">
        <div className="section-header">
          <h2>Recent documents</h2>
          <button className="btn btn-secondary" onClick={() => onNavigate("documents")}>
            View all
          </button>
        </div>

        {recent.length === 0 ? (
          <div className="empty-state-v2">
            <div className="icon-wrap"><FileText size={20} /></div>
            <strong>No documents yet</strong>
            <span>Upload your first financial report to get started.</span>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((doc) => {
                const cfg = STATUS_CONFIG[doc.status] || STATUS_CONFIG.uploaded;
                return (
                  <tr key={doc.document_id}>
                    <td>
                      <div className="doc-cell">
                        <div className="doc-icon"><FileText size={15} /></div>
                        <span className="doc-name">{doc.filename}</span>
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

function KpiCard({ label, value }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value num">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}