import { useState } from "react";
import UploadZone from "./components/UploadZone";

function App() {
  const [documentId, setDocumentId] = useState(null);

  return (
    <div style={{ maxWidth: "600px", margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Financial AI Agent</h1>

      <UploadZone onDocumentReady={(id) => setDocumentId(id)} />

      {documentId && (
        <p style={{ marginTop: "16px" }}>
          Document prêt à être traité : <code>{documentId}</code>
        </p>
      )}
    </div>
  );
}

export default App;