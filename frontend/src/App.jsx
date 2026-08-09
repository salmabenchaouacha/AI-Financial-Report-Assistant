import { useEffect, useState } from "react";
import { checkHealth } from "./api/client";

function App() {
  const [backendStatus, setBackendStatus] = useState("Vérification...");

  useEffect(() => {
    checkHealth()
      .then((data) => setBackendStatus(`✅ Backend connecté : ${data.status}`))
      .catch(() => setBackendStatus("❌ Impossible de contacter le backend"));
  }, []);

  return (
    <div style={{ maxWidth: "600px", margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Financial AI Agent</h1>
      <p>{backendStatus}</p>
    </div>
  );
}

export default App;