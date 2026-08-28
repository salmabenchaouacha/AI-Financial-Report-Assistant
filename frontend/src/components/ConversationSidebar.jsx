import { Plus, MessageSquare } from "lucide-react";

export default function ConversationSidebar({ conversations, activeId, onSelect, onNew }) {
  return (
    <div className="conv-sidebar">
      <button className="btn btn-secondary" style={{ width: "100%", justifyContent: "center", marginBottom: 12 }} onClick={onNew}>
        <Plus size={14} /> New conversation
      </button>
      <div className="conv-sidebar-list">
        {conversations.length === 0 && (
          <div className="empty-state-v2" style={{ padding: "30px 10px" }}>
            <MessageSquare size={18} />
            <span>No conversations yet.</span>
          </div>
        )}
        {conversations.map((c) => (
          <div
            key={c.conversation_id}
            className={`conv-item ${c.conversation_id === activeId ? "active" : ""}`}
            onClick={() => onSelect(c.conversation_id)}
          >
            <div className="conv-item-title">{c.title}</div>
            <div className="conv-item-date">
              {new Date(c.updated_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}