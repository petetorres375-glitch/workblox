import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { usePWA } from "../../hooks/usePWA";

function InstallModal({ onClose }) {
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000, padding: "1rem",
    }} onClick={onClose}>
      <div style={{
        background: "#1e293b", borderRadius: "12px", padding: "1.5rem",
        maxWidth: "320px", width: "100%", color: "#fff",
      }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: "0 0 0.75rem", fontSize: "1rem", color: "#93c5fd" }}>
          Install Workblox Business
        </h3>
        <p style={{ fontSize: "0.85rem", color: "#cbd5e1", marginBottom: "1rem", lineHeight: 1.6 }}>
          To install on Android:
        </p>
        <ol style={{ fontSize: "0.85rem", color: "#cbd5e1", lineHeight: 2, paddingLeft: "1.2rem", margin: "0 0 1.25rem" }}>
          <li>Tap the <strong style={{ color: "#fff" }}>⋮ three-dot menu</strong> in Chrome</li>
          <li>Tap <strong style={{ color: "#fff" }}>"Add to Home screen"</strong></li>
          <li>Tap <strong style={{ color: "#fff" }}>"Add"</strong></li>
        </ol>
        <button onClick={onClose} style={{
          width: "100%", background: "#2563eb", color: "#fff", border: "none",
          borderRadius: "8px", padding: "0.65rem", fontSize: "0.9rem",
          fontFamily: "inherit", cursor: "pointer", fontWeight: 600,
        }}>Got it</button>
      </div>
    </div>
  );
}

const NAV_ITEMS = [
  { id: "hiring", label: "Hiring Manager" },
  { id: "batch-ats", label: "Batch ATS" },
  { id: "job-desc", label: "Job Description" },
  { id: "proposal", label: "Proposal" },
  { id: "contract", label: "Contract" },
  { id: "customer", label: "Customer Response" },
  { id: "review", label: "Review Request" },
  { id: "social", label: "Social Media" },
  { id: "ad-copy", label: "Ad Copy" },
  { id: "policy", label: "Policy" },
  { id: "sop", label: "SOP" },
  { id: "meeting", label: "Meeting Notes" },
  { id: "email", label: "Business Email" },
  { id: "contacts", label: "Contacts" },
];

export default function Header({ active, onSelect }) {
  const { user, logout } = useAuth();
  const { canInstall, install } = usePWA();
  const [showInstallModal, setShowInstallModal] = useState(false);

  function handleInstall() {
    if (canInstall) install();
    else setShowInstallModal(true);
  }

  return (
    <header className="site-header">
      <div className="header-top">
        <div className="brand">
          <span className="brand-name">
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <div className="brand-divider" />
          <span className="brand-product">Workblox Business</span>
        </div>
        <div className="header-user">
          <span className="header-user-name">{user?.name}</span>
          <button className="header-install" onClick={handleInstall}>⊕ Install</button>
          <button className="header-signout" onClick={logout}>Sign out</button>
        </div>
      </div>
      {showInstallModal && <InstallModal onClose={() => setShowInstallModal(false)} />}
      <nav className="tool-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={active === item.id ? "active" : ""}
            onClick={() => onSelect(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
