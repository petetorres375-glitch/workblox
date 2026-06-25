import { usePWA } from "../../hooks/usePWA";

export default function Header({ title }) {
  const { canInstall, install } = usePWA();

  return (
    <header
      style={{
        borderBottom: "1px solid var(--color-border)",
        padding: "14px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "var(--color-surface)",
      }}
    >
      <span style={{ fontSize: "0.95rem", fontWeight: 500, color: "var(--color-text-muted)" }}>{title}</span>
      {canInstall && (
        <button
          onClick={install}
          style={{
            background: "var(--color-accent)",
            border: "none",
            borderRadius: "var(--radius)",
            color: "#fff",
            fontSize: "0.8rem",
            fontWeight: 600,
            padding: "6px 14px",
            cursor: "pointer",
          }}
        >
          Install App
        </button>
      )}
    </header>
  );
}
