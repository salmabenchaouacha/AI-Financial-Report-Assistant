import { useState } from "react";
import { Sparkles } from "lucide-react";
import ChatWindow from "../components/ChatWindow";

export default function AnalysisPage({ documents, selectedIds, onToggle, conversationId, onConversationChange, onConversationsUpdated }) {
  const [started, setStarted] = useState(!!conversationId);

  if (started) {
    return (
      <ChatWindow
        documents={documents}
        documentIds={selectedIds}
        conversationId={conversationId}
        onConversationChange={onConversationChange}
        onConversationsUpdated={onConversationsUpdated}
      />
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Ask your financial data</h1>
          <p>Select the reports you want to analyze, then ask a question in plain language.</p>
        </div>
      </div>

      <div className="section">
        <div className="analysis-composer">
          <div className="answer-eyebrow" style={{ marginBottom: 10 }}>Documents</div>
          <div className="doc-select-row">
            {documents.filter((d) => d.status === "indexed").map((d) => (
              <div
                key={d.document_id}
                className={`doc-select-chip ${selectedIds.includes(d.document_id) ? "selected" : ""}`}
                onClick={() => onToggle(d.document_id)}
              >
                {d.filename}
              </div>
            ))}
          </div>

          <div className="answer-eyebrow" style={{ marginBottom: 10 }}>Question</div>
          <textarea
            id="analysis-question"
            placeholder="Ask a question about your financial reports…"
          />

          <div style={{ marginTop: 14, display: "flex", justifyContent: "flex-end" }}>
            <button
              className="btn btn-primary"
              disabled={selectedIds.length === 0}
              onClick={() => setStarted(true)}
            >
              <Sparkles size={15} /> Generate analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}