export default function ConversationList({ conversations, activeId, onSelect, onNew }) {
  return (
    <div className="doc-list">
      <div className="doc-list-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>Discussions</span>
        <button className="new-chat-btn" onClick={onNew}>+ Nouvelle</button>
      </div>

      {conversations.length === 0 && (
        <p style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>Aucune discussion pour l'instant.</p>
      )}

      {conversations.map((c) => (
        <div
          key={c.conversation_id}
          className={`conv-card ${c.conversation_id === activeId ? "selected" : ""}`}
          onClick={() => onSelect(c.conversation_id)}
        >
          <span className="conv-title">{c.title}</span>
          <span className="conv-date">
            {new Date(c.updated_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" })}
          </span>
        </div>
      ))}
    </div>
  );
}