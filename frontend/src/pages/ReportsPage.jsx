import { useEffect, useState } from "react";
import { Download, Maximize2, BarChart3 } from "lucide-react";
import { listReports } from "../api/client";

export default function ReportsPage() {
  const [reports, setReports] = useState([]);

  useEffect(() => { listReports().then((d) => setReports(d.reports)); }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Financial Visualization</h1>
          <p>All charts generated from your reports, in one place.</p>
        </div>
      </div>

      {reports.length === 0 ? (
        <div className="section">
          <div className="empty-state-v2">
            <div className="icon-wrap"><BarChart3 size={20} /></div>
            <strong>No charts yet</strong>
            <span>Generate a chart from the Analysis page to see it here.</span>
          </div>
        </div>
      ) : (
        <div className="reports-grid">
          {reports.map((r) => (
            <div className="report-card" key={r.id}>
              <div className="report-card-image">
                <img src={`http://localhost:5000${r.chart_url}`} alt={r.question} />
              </div>
              <div className="report-card-body">
                <div className="report-card-title">{r.question}</div>
                <div className="doc-sub">{r.filename}</div>
                <div className="report-card-meta">
                  <span>{new Date(r.created_at).toLocaleDateString("fr-FR")}</span>
                  <div style={{ display: "flex", gap: 6 }}>
                    <a className="icon-btn" href={`http://localhost:5000${r.chart_url}`} target="_blank" rel="noreferrer">
                      <Maximize2 size={13} />
                    </a>
                    <a className="icon-btn" href={`http://localhost:5000${r.chart_url}`} download>
                      <Download size={13} />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}