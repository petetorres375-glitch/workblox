export default function Card({ children, style }) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "20px",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
