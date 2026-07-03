import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import { usePWA } from "../../hooks/usePWA";
import LanguageSwitcher from "./LanguageSwitcher";

function InstallModal({ onClose }) {
  const { t } = useTranslation("common");
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
          {t("installModal.title")}
        </h3>
        <p style={{ fontSize: "0.85rem", color: "#cbd5e1", marginBottom: "1rem", lineHeight: 1.6 }}>
          {t("installModal.intro")}
        </p>
        <ol style={{ fontSize: "0.85rem", color: "#cbd5e1", lineHeight: 2, paddingLeft: "1.2rem", margin: "0 0 1.25rem" }}>
          <li><Trans t={t} i18nKey="installModal.step1"><strong style={{ color: "#fff" }}>⋮ three-dot menu</strong></Trans></li>
          <li><Trans t={t} i18nKey="installModal.step2"><strong style={{ color: "#fff" }}>"Add to Home screen"</strong></Trans></li>
          <li><Trans t={t} i18nKey="installModal.step3"><strong style={{ color: "#fff" }}>"Add"</strong></Trans></li>
        </ol>
        <button onClick={onClose} style={{
          width: "100%", background: "#2563eb", color: "#fff", border: "none",
          borderRadius: "8px", padding: "0.65rem", fontSize: "0.9rem",
          fontFamily: "inherit", cursor: "pointer", fontWeight: 600,
        }}>{t("installModal.gotIt")}</button>
      </div>
    </div>
  );
}

const NAV_IDS = [
  "ad-copy", "batch-ats", "email", "contacts", "contract", "customer",
  "hiring", "job-desc", "meeting", "policy", "proposal", "review", "social", "sop",
];

export default function Header({ active, onSelect }) {
  const { t } = useTranslation(["nav", "common"]);
  const { user, logout } = useAuth();
  const { canInstall, install, isInstalled } = usePWA();
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
          <LanguageSwitcher />
          {!isInstalled && <button className="header-install" onClick={handleInstall}>⊕ {t("common:install")}</button>}
          <button className="header-signout" onClick={logout}>{t("common:signOut")}</button>
        </div>
      </div>
      {showInstallModal && <InstallModal onClose={() => setShowInstallModal(false)} />}
      <nav className="tool-nav">
        {NAV_IDS.map((id) => (
          <button
            key={id}
            className={active === id ? "active" : ""}
            onClick={() => onSelect(id)}
          >
            {t(`nav:${id}`)}
          </button>
        ))}
      </nav>
    </header>
  );
}
