import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, BarChart3, Paperclip, X, BookmarkPlus, BookmarkCheck } from "lucide-react";
import { askQuestion, generateChart, getConversation, chatWithUpload, saveToReport, listConversations } from "../api/client";
import LoadingMessage from "./LoadingMessage";
import KeyFigures from "./KeyFigures";
import SourceChips from "./SourceChips";
import ConversationSidebar from "./ConversationSidebar";

const CHAT_MESSAGES = ["Consultation du dossier…", "Vérification des chiffres…", "Rédaction de la réponse…"];
const CHART_MESSAGES = ["Esquisse du graphique…", "Calibrage des axes…", "Mise en couleur…"];
const UPLOAD_MESSAGES = ["Lecture du document joint…", "Indexation en cours…", "Presque prêt…"];

export default function ChatWindow({ documents, documentIds, conversationId, onConversationChange, onConversationsUpdated, onDocumentsChanged }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(null);
  const [attachedFile, setAttachedFile] = useState(null);
  const [conversations, setConversations] = useState([]);
  const fileInputRef = useRef(null);

  const selectedFilenames = documents
    .filter((d) => documentIds.includes(d.document_id))
    .map((d) => d.filename);

  const refreshConvList = async () => {
    const data = await listConversations();
    setConversations(data.conversations);
  };

  useEffect(() => { refreshConvList(); }, []);

  useEffect(() => {
    if (!conversationId) { setMessages([]); return; }
    getConversation(conversationId).then((data) => {
      const loaded = [];
      data.messages.forEach((m) => {
        loaded.push({ role: "question", text: m.question });
        loaded.push({
          role: "answer",
          messageId: m.id,
          text: m.answer,
          sources: m.sources,
          chartUrl: m.chart_url ? `http://localhost:5000${m.chart_url}?t=${Date.now()}` : undefined,
          savedToReport: m.saved_to_report,
        });
      });
      setMessages(loaded);
    });
  }, [conversationId]);

  const send = async (mode) => {
    if (!input.trim() || pending) return;
    if (!attachedFile && !conversationId && documentIds.length === 0) return;

    const question = input.trim();
    setMessages((m) => [...m, { role: "question", text: question }]);
    setInput("");

    if (attachedFile) {
      setPending("upload");
      const fileToSend = attachedFile;
      setAttachedFile(null);
      try {
        const data = await chatWithUpload(fileToSend, question, conversationId);
        setMessages((m) => [...m, { role: "answer", text: data.answer, sources: data.sources }]);
        if (!conversationId) onConversationChange(data.conversation_id);
        onDocumentsChanged?.();
        refreshConvList();
        onConversationsUpdated?.();
      } catch {
        setMessages((m) => [...m, { role: "answer", text: "Une erreur est survenue lors de l'import du document." }]);
      } finally {
        setPending(null);
      }
      return;
    }

    setPending(mode);
    try {
      if (mode === "chart") {
        const data = await generateChart(documentIds, question, conversationId);
        setMessages((m) => [...m, {
          role: "answer",
          chartUrl: `http://localhost:5000${data.chart_url}?t=${Date.now()}`,
          messageId: data.message_id,
          savedToReport: false,
        }]);
        if (!conversationId) onConversationChange(data.conversation_id);
      } else {
        const data = await askQuestion(documentIds, question, conversationId);
        setMessages((m) => [...m, { role: "answer", text: data.answer, sources: data.sources }]);
        if (!conversationId) onConversationChange(data.conversation_id);
      }
      refreshConvList();
      onConversationsUpdated?.();
    } catch {
      setMessages((m) => [...m, { role: "answer", text: "Une erreur est survenue. Réessayez." }]);
    } finally {
      setPending(null);
    }
  };

  const handleAddToReport = async (index, messageId) => {
    if (!messageId) return;
    await saveToReport(messageId);
    setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, savedToReport: true } : msg)));
  };

  const canSend = input.trim() && !pending && (attachedFile || conversationId || documentIds.length > 0);

  return (
    <div className="chat-page-layout">
      <ConversationSidebar
        conversations={conversations}
        activeId={conversationId}
        onSelect={onConversationChange}
        onNew={() => onConversationChange(null)}
      />

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
              <span>Select a document, or attach a PDF directly below.</span>
            </div>
          )}

          {messages.map((m, i) =>
            m.role === "question" ? (
              <div className="msg-question" key={i}>{m.text}</div>
            ) : (
              <div className="msg-answer" key={i}>
                {m.chartUrl ? (
                  <>
                    <img src={m.chartUrl} alt="Généré" style={{ width: "100%", borderRadius: 8 }} />
                    <div className="chart-actions">
                      {m.savedToReport ? (
                        <button className="btn btn-secondary" disabled>
                          <BookmarkCheck size={14} /> Added to report
                        </button>
                      ) : (
                        <button className="btn btn-primary" onClick={() => handleAddToReport(i, m.messageId)}>
                          <BookmarkPlus size={14} /> Add to report
                        </button>
                      )}
                    </div>
                  </>
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
              <LoadingMessage messages={pending === "chart" ? CHART_MESSAGES : pending === "upload" ? UPLOAD_MESSAGES : CHAT_MESSAGES} />
            </div>
          )}
        </div>

        <div className="chat-composer">
          <div className="chat-composer-inner" style={{ flexDirection: "column", alignItems: "stretch" }}>
            {attachedFile && (
              <div className="attached-file-chip">
                <Paperclip size={12} /> {attachedFile.name}
                <button onClick={() => setAttachedFile(null)}><X size={13} /></button>
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <input type="file" accept="application/pdf" ref={fileInputRef} style={{ display: "none" }}
                onChange={(e) => e.target.files[0] && setAttachedFile(e.target.files[0])} />
              <button className="attach-btn" onClick={() => fileInputRef.current?.click()}>
                <Paperclip size={15} />
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send("chat")}
                placeholder="Ask a question, or attach a PDF to start…"
                disabled={!attachedFile && !conversationId && documentIds.length === 0}
              />
              <button className="btn btn-secondary" onClick={() => send("chart")} disabled={!canSend || !!attachedFile}>
                <BarChart3 size={15} />
              </button>
              <button className="btn btn-primary" onClick={() => send("chat")} disabled={!canSend}>
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}