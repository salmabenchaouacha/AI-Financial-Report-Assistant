import { useState } from "react";
import UploadZone from "./components/UploadZone";
import ChatWindow from "./components/ChatWindow";

function App() {
  const [documentId, setDocumentId] = useState(null);

  return (
    <div style={{ maxWidth: "700px", margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Financial AI Agent</h1>

      <UploadZone onDocumentReady={(id) => setDocumentId(id)} />

      {documentId && <ChatWindow documentId={documentId} />}
    </div>
  );
}

export default App;