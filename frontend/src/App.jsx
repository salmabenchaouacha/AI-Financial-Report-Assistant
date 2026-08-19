import { useEffect, useState } from "react";
import { listDocuments } from "./api/client";
import UploadZone from "./components/UploadZone";
import DocumentList from "./components/DocumentList";
import ChatWindow from "./components/ChatWindow";
import "./theme.css";

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);

  const refresh = async () => {
    const data = await listDocuments();
    setDocuments(data.documents);
  };

  useEffect(() => { refresh(); }, []);

  const toggle = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm("Voulez-vous vraiment supprimer ce document ?")) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:5000/api/upload/documents/${documentId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Erreur lors de la suppression");
      }

      // Supprimer le document de la liste affichée
      setDocuments((prev) =>
        prev.filter((doc) => doc.document_id !== documentId)
      );

      // S'il était sélectionné, le retirer aussi
      setSelectedIds((prev) =>
        prev.filter((id) => id !== documentId)
      );

    } catch (error) {
      console.error("Erreur suppression :", error);
      alert(error.message);
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">Analyse documentaire</span>
          <h1>Sonde</h1>
          <p>Déposez un document, envoyez un signal, obtenez une réponse précise.</p>
        </div>

        <UploadZone onDocumentsIndexed={refresh} />
        <DocumentList
          documents={documents}
          selectedIds={selectedIds}
          onToggle={toggle}
          onDelete={deleteDocument}
        />
      </aside>

      <ChatWindow documentIds={selectedIds} />
    </div>
  );
}

export default App;

