export default function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div
      style={{
        background: "rgba(239,68,68,0.1)",
        border: "1px solid var(--color-danger)",
        borderRadius: "var(--radius)",
        padding: "12px 16px",
        color: "var(--color-danger)",
        fontSize: "0.9rem",
        marginTop: 16,
      }}
    >
      {message}
    </div>
  );
}
