import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { askQuestion, generateChart } from "../api/client";
import LoadingMessage from "./LoadingMessage";
import SourcePanel from "./SourcePanel";

const CHAT_MESSAGES = ["Consultation du dossier…", "Vérification des chiffres…", "Rédaction de la réponse…"];
const CHART_MESSAGES = ["Esquisse du graphique…", "Calibrage des axes…", "Mise en couleur…"];
const CHART_TYPE_LABELS = {
  evolution: "Courbe d'évolution",
  comparaison: "Comparaison",
  classement: "Classement",
  repartition: "Répartition",
  difference: "Écart",
  valeur_unique: "Valeur unique",
};
export default function ChatWindow({ documentIds }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(null);
  const [openAudit, setOpenAudit] = useState({});

  const send = async (mode) => {
    if (!input.trim() || documentIds.length === 0 || pending) return;
    const question = input.trim();
    setMessages((m) => [...m, { role: "question", text: question }]);
    setInput("");
    setPending(mode);

    try {
      if (mode === "chart") {
        const data = await generateChart(documentIds, question);
        setMessages((m) => [
          ...m,
          { role: "answer", text: "Voici le graphique demandé.",  chartUrl: `http://localhost:5000${data.chart_url}?t=${Date.now()}`,chartType: data.chart_type_detected },
        ]);
      } else {
        const data = await askQuestion(documentIds, question);
        setMessages((m) => [...m, { role: "answer", text: data.answer, sources: data.sources }]);
      }
    } catch (err) {
      setMessages((m) => [...m, { role: "answer", text: "Une erreur est survenue. Réessayez." }]);
    } finally {
      setPending(null);
    }
  };

  const toggleAudit = (i) => setOpenAudit((o) => ({ ...o, [i]: !o[i] }));

  return (
    <div className="main">
      <div className="main-header">
        <h2>Consultation du dossier</h2>
        <span className="selection-hint">
          {documentIds.length === 0
            ? "Aucun document sélectionné"
            : `${documentIds.length} document${documentIds.length > 1 ? "s" : ""} sélectionné${documentIds.length > 1 ? "s" : ""}`}
        </span>
      </div>

      <div className="thread">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="glyph">§</div>
            <p>Sélectionnez un ou plusieurs dossiers, puis posez votre question.</p>
          </div>
        )}

        {messages.map((m, i) => (
          <div className={`slip ${m.role}`} key={i}>
            {m.role === "question" ? (
              m.text
            ) : (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
              </div>
            )}

             {m.chartUrl && (
              <>
                {m.chartType && (
                  <span className="chart-type-badge">{CHART_TYPE_LABELS[m.chartType] || m.chartType}</span>
                )}
                <div className="chart-frame">
                  <img src={m.chartUrl} alt="Graphique généré" />
                </div>
              </>
            )}

            {m.role === "answer" && !m.chartUrl && (
              <>
                <div className="stamp">✓ Vérifié sur pièce</div>
                {m.sources && m.sources.length > 0 && (
                  <button className="audit-toggle" onClick={() => toggleAudit(i)}>
                    {openAudit[i] ? "Masquer les sources ▴" : `Voir les sources (${m.sources.length}) ▾`}
                  </button>
                )}
                {openAudit[i] && <SourcePanel sources={m.sources} answerText={m.text} />}
              </>
            )}
          </div>
        ))}

        {pending && (
          <div className="slip answer">
            <LoadingMessage messages={pending === "chart" ? CHART_MESSAGES : CHAT_MESSAGES} />
          </div>
        )}
      </div>

      <div className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send("chat")}
          placeholder="Quel est le total du bilan de…"
          disabled={documentIds.length === 0}
        />
        <button className="secondary" onClick={() => send("chart")} disabled={!input.trim() || pending}>
          Graphique
        </button>
        <button className="primary" onClick={() => send("chat")} disabled={!input.trim() || pending}>
          Envoyer
        </button>
      </div>
    </div>
  );
}