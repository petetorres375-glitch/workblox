export default function Footer() {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--color-border)",
        padding: "12px 32px",
        fontSize: "0.78rem",
        color: "var(--color-text-muted)",
        display: "flex",
        gap: 6,
      }}
    >
      <span>Workblox</span>
      <span>·</span>
      <a href="https://petetorres375-glitch.github.io/torres-tech-remote/" target="_blank" rel="noreferrer">
        Torres Tech Remote
      </a>
    </footer>
  );
}
