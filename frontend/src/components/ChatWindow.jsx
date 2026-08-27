import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, BarChart3 } from "lucide-react";
import { askQuestion, generateChart, getConversation } from "../api/client";
import LoadingMessage from "./LoadingMessage";
import KeyFigures from "./KeyFigures";
import SourceChips from "./SourceChips";

const CHAT_MESSAGES = ["Consultation du dossier…", "Vérification des chiffres…", "Rédaction de la réponse…"];
const CHART_MESSAGES = ["Esquisse du graphique…", "Calibrage des axes…", "Mise en couleur…"];

export default function ChatWindow({ documents, documentIds, conversationId, onConversationChange, onConversationsUpdated }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(null);

  const selectedFilenames = documents
    .filter((d) => documentIds.includes(d.document_id))
    .map((d) => d.filename);

  useEffect(() => {
    if (!conversationId) { setMessages([]); return; }
    getConversation(conversationId).then((data) => {
      const loaded = [];
      data.messages.forEach((m) => {
        loaded.push({ role: "question", text: m.question });
        loaded.push({
          role: "answer",
          text: m.answer,
          sources: m.sources,
          chartUrl: m.chart_url ? `http://localhost:5000${m.chart_url}?t=${Date.now()}` : undefined,
        });
      });
      setMessages(loaded);
    });
  }, [conversationId]);

  const send = async (mode) => {
    if (!input.trim() || pending) return;
    if (!conversationId && documentIds.length === 0) return;

    const question = input.trim();
    setMessages((m) => [...m, { role: "question", text: question }]);
    setInput("");
    setPending(mode);

    try {
      if (mode === "chart") {
        const data = await generateChart(documentIds, question, conversationId);
        setMessages((m) => [...m, {
          role: "answer",
          text: "Voici le graphique demandé.",
          chartUrl: `http://localhost:5000${data.chart_url}?t=${Date.now()}`,
        }]);
        if (!conversationId) onConversationChange(data.conversation_id);
      } else {
        const data = await askQuestion(documentIds, question, conversationId);
        setMessages((m) => [...m, { role: "answer", text: data.answer, sources: data.sources }]);
        if (!conversationId) onConversationChange(data.conversation_id);
      }
      onConversationsUpdated?.();
    } catch {
      setMessages((m) => [...m, { role: "answer", text: "Une erreur est survenue. Réessayez." }]);
    } finally {
      setPending(null);
    }
  };

  const canSend = input.trim() && !pending && (conversationId || documentIds.length > 0);

  return (
    <div className="chat-shell">
      <div className="chat-header">
        <div className="chat-header-left">
          <h2>Financial Analyst</h2>
          <span className="ready-indicator"><span className="ready-dot" />Ready</span>
        </div>
        <div className="doc-pills">
          {selectedFilenames.map((f, i) => <span className="doc-pill" key={i}>{f}</span>)}
        </div>
      </div>

      <div className="chat-thread">
        {messages.length === 0 && (
          <div className="empty-state-v2">
            <strong>Ask your financial data</strong>
            <span>Select documents, then ask a question to start the conversation.</span>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "question" ? (
            <div className="msg-question" key={i}>{m.text}</div>
          ) : (
            <div className="msg-answer" key={i}>
              {m.chartUrl ? (
                <img src={m.chartUrl} alt="Généré" style={{ width: "100%", borderRadius: 8 }} />
              ) : (
                <>
                  <div className="answer-block">
                    <div className="answer-eyebrow">Answer</div>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                  </div>
                  <KeyFigures answerText={m.text} />
                  <SourceChips sources={m.sources} answerText={m.text} />
                </>
              )}
            </div>
          )
        )}

        {pending && (
          <div className="msg-answer">
            <LoadingMessage messages={pending === "chart" ? CHART_MESSAGES : CHAT_MESSAGES} />
          </div>
        )}
      </div>

      <div className="chat-composer">
        <div className="chat-composer-inner">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send("chat")}
            placeholder="Ask a question about your financial reports…"
            disabled={!conversationId && documentIds.length === 0}
          />
          <button className="btn btn-secondary" onClick={() => send("chart")} disabled={!canSend}>
            <BarChart3 size={15} />
          </button>
          <button className="btn btn-primary" onClick={() => send("chat")} disabled={!canSend}>
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}