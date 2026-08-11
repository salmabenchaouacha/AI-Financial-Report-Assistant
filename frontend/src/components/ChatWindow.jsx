import { useState } from "react";
import { askQuestion, generateChart } from "../api/client";

const API_ORIGIN = "http://localhost:5000";

export default function ChatWindow({ documentId }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]); // { question, answer, chartUrl, loading }

  const handleAsk = async () => {
    if (!question.trim()) return;

    const currentQuestion = question;
    setQuestion("");

    const newMessage = { question: currentQuestion, answer: null, chartUrl: null, loading: true };
    setMessages((prev) => [...prev, newMessage]);

    try {
      const data = await askQuestion(documentId, currentQuestion);
      updateLastMessage({ answer: data.answer, loading: false });
    } catch (err) {
      updateLastMessage({
        answer: "❌ Erreur : " + (err.response?.data?.error || "impossible de répondre"),
        loading: false,
      });
    }
  };

  const handleGenerateChart = async (index, questionText) => {
    updateMessageAt(index, { chartLoading: true });
    try {
      const data = await generateChart(documentId, questionText);
      updateMessageAt(index, { chartUrl: API_ORIGIN + data.chart_url, chartLoading: false });
    } catch (err) {
      updateMessageAt(index, {
        chartError: err.response?.data?.error || "Erreur génération graphique",
        chartLoading: false,
      });
    }
  };

  const updateLastMessage = (updates) => {
    setMessages((prev) => {
      const copy = [...prev];
      copy[copy.length - 1] = { ...copy[copy.length - 1], ...updates };
      return copy;
    });
  };

  const updateMessageAt = (index, updates) => {
    setMessages((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], ...updates };
      return copy;
    });
  };

  return (
    <div style={{ marginTop: "24px" }}>
      <h3>Poser une question sur le rapport</h3>

      <div style={{ display: "flex", gap: "8px" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="Ex: Quel est le total du bilan de CBI Burkina Faso ?"
          style={{ flex: 1, padding: "8px" }}
        />
        <button onClick={handleAsk}>Envoyer</button>
      </div>

      <div style={{ marginTop: "16px" }}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{ border: "1px solid #eee", borderRadius: "8px", padding: "12px", marginBottom: "12px" }}
          >
            <p><strong>Q :</strong> {msg.question}</p>

            {msg.loading ? (
              <p>⏳ Réflexion en cours...</p>
            ) : (
              <>
                <p><strong>R :</strong> {msg.answer}</p>

                {!msg.chartUrl && !msg.chartLoading && (
                  <button onClick={() => handleGenerateChart(index, msg.question)}>
                    📊 Générer un graphique pour cette question
                  </button>
                )}

                {msg.chartLoading && <p>⏳ Génération du graphique...</p>}

                {msg.chartError && <p style={{ color: "red" }}>❌ {msg.chartError}</p>}

                {msg.chartUrl && (
                  <img
                    src={msg.chartUrl}
                    alt="Graphique généré"
                    style={{ maxWidth: "100%", marginTop: "8px", border: "1px solid #ddd" }}
                  />
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}