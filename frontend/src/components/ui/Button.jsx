export default function Button({ children, onClick, disabled, variant = "primary", type = "button" }) {
  const styles = {
    primary: {
      background: disabled ? "#e8e4de" : "var(--color-accent)",
      color: disabled ? "var(--color-text-muted)" : "#fff",
      border: "none",
      cursor: disabled ? "not-allowed" : "pointer",
    },
    secondary: {
      background: "transparent",
      color: "var(--color-text-muted)",
      border: "1px solid var(--color-border)",
      cursor: disabled ? "not-allowed" : "pointer",
    },
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: "10px 20px",
        borderRadius: "var(--radius)",
        fontSize: "0.9rem",
        fontWeight: 600,
        transition: "opacity 0.15s",
        ...styles[variant],
      }}
    >
      {children}
    </button>
  );
}
