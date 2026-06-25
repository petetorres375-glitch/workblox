const TOOLS = [
  { id: "doc", label: "Doc Analyzer", icon: "📄" },
  { id: "workflow", label: "Workflow Builder", icon: "⚙️" },
  { id: "linux", label: "Linux Helper", icon: "🐧" },
  { id: "windows", label: "Windows Helper", icon: "🪟" },
  { id: "mac", label: "Mac Helper", icon: "🍎" },
];

export default function Sidebar({ active, onSelect }) {
  return (
    <aside
      style={{
        width: "var(--sidebar-width)",
        background: "var(--color-surface)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        padding: "24px 0",
        flexShrink: 0,
      }}
    >
      <div style={{ padding: "0 20px 24px", borderBottom: "1px solid var(--color-border)" }}>
        <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--color-text)" }}>Workblox</div>
        <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: 2 }}>Torres Tech Remote</div>
      </div>
      <nav style={{ padding: "16px 8px", display: "flex", flexDirection: "column", gap: 4 }}>
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => onSelect(tool.id)}
            style={{
              background: active === tool.id ? "rgba(99,102,241,0.15)" : "transparent",
              border: active === tool.id ? "1px solid rgba(99,102,241,0.35)" : "1px solid transparent",
              borderRadius: "var(--radius)",
              color: active === tool.id ? "var(--color-text)" : "var(--color-text-muted)",
              cursor: "pointer",
              padding: "9px 12px",
              textAlign: "left",
              fontSize: "0.88rem",
              fontWeight: active === tool.id ? 600 : 400,
              display: "flex",
              alignItems: "center",
              gap: 10,
              transition: "all 0.12s",
            }}
          >
            <span>{tool.icon}</span>
            {tool.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
