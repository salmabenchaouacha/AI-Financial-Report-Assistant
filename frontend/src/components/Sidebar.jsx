import { LayoutDashboard, FileText, Sparkles, MessageSquare, BarChart3, Settings } from "lucide-react";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "analysis", label: "Analysis", icon: Sparkles },
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "reports", label: "Reports", icon: BarChart3 },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar-v2">
      <div className="sidebar-brand">
        <div className="mark">
          <Sparkles size={16} />
        </div>
        <span className="brand-text">Financial AI</span>
      </div>

      <nav className="nav-section">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${activePage === id ? "active" : ""}`}
            onClick={() => onNavigate(id)}
          >
            <Icon size={17} />
            <span className="nav-label">{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item">
          <Settings size={17} />
          <span className="nav-label">Settings</span>
        </button>
        <div className="user-row">
          <div className="user-avatar">SA</div>
          <div className="user-text">
            <span className="user-name">Analyste</span>
            <span className="user-role">Compte gratuit</span>
          </div>
        </div>
      </div>
    </aside>
  );
}