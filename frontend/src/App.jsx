import { useEffect, useState } from "react";
import { listDocuments, listConversations } from "./api/client";
import Sidebar from "./components/Sidebar";
import UploadModal from "./components/UploadModal";
import OverviewPage from "./pages/OverviewPage";
import DocumentsPage from "./pages/DocumentsPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import ChatWindow from "./components/ChatWindow";
import "./theme.css";

function App() {
  const [page, setPage] = useState("overview");
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [showUpload, setShowUpload] = useState(false);

  const refreshDocuments = async () => setDocuments((await listDocuments()).documents);
  const refreshConversations = async () => setConversations((await listConversations()).conversations);

  useEffect(() => { refreshDocuments(); refreshConversations(); }, []);

  const toggle = (id) => setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="app-shell-v2">
      <Sidebar activePage={page} onNavigate={setPage} />

      {page === "overview" && (
        <OverviewPage documents={documents} onNavigate={setPage} onUploadClick={() => setShowUpload(true)} />
      )}

      {page === "documents" && (
        <DocumentsPage documents={documents} selectedIds={selectedIds} onToggle={toggle} onAnalyze={() => setPage("analysis")} />
      )}

      {page === "analysis" && (
        <AnalysisPage
          documents={documents}
          selectedIds={selectedIds}
          onToggle={toggle}
          conversationId={activeConversationId}
          onConversationChange={setActiveConversationId}
          onConversationsUpdated={refreshConversations}
        />
      )}

      {page === "chat" && (
        <ChatWindow
          documents={documents}
          documentIds={selectedIds}
          conversationId={activeConversationId}
          onConversationChange={setActiveConversationId}
          onConversationsUpdated={refreshConversations}
        />
      )}

      {page === "reports" && <ReportsPage />}

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onDone={() => { refreshDocuments(); }}
        />
      )}
    </div>
  );
}

export default App;