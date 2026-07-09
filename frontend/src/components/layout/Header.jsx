import { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import { usePWA } from "../../hooks/usePWA";
import LanguageSwitcher from "./LanguageSwitcher";

function MenuIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="19" y2="6" />
      <line x1="3" y1="11" x2="19" y2="11" />
      <line x1="3" y1="16" x2="19" y2="16" />
    </svg>
  );
}

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
        <h3 style={{ margin: "0 0 0.75rem", fontSize: "1rem", color: "#fbbf9a" }}>
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
          width: "100%", background: "#e05c2e", color: "#fff", border: "none",
          borderRadius: "8px", padding: "0.65rem", fontSize: "0.9rem",
          fontFamily: "inherit", cursor: "pointer", fontWeight: 600,
        }}>{t("installModal.gotIt")}</button>
      </div>
    </div>
  );
}

// To exercise this locally with Playwright, run `npx playwright install chromium`
// (no --with-deps — that shells out to sudo apt, which fails without a TTY here).
function LinuxTrustTip({ onClose }) {
  const { t } = useTranslation("common");
  return (
    <div style={{
      position: "fixed", bottom: "1rem", right: "1rem", maxWidth: "340px",
      background: "#1e293b", borderRadius: "12px", padding: "1.25rem",
      color: "#fff", zIndex: 1000, boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
    }}>
      <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem", color: "#fbbf9a" }}>
        {t("linuxTrustTip.title")}
      </h3>
      <p style={{ fontSize: "0.8rem", color: "#cbd5e1", lineHeight: 1.6, marginBottom: "0.75rem" }}>
        {t("linuxTrustTip.body")}
      </p>
      <pre style={{
        background: "#0f172a", borderRadius: "8px", padding: "0.6rem 0.75rem",
        fontSize: "0.72rem", color: "#93c5fd", margin: "0 0 1rem",
        whiteSpace: "pre-wrap", wordBreak: "break-all",
      }}>
{"chmod +x ~/.local/share/applications/chrome-*.desktop\ngio set ~/.local/share/applications/chrome-*.desktop metadata::trusted true"}
      </pre>
      <button onClick={onClose} style={{
        width: "100%", background: "#e05c2e", color: "#fff", border: "none",
        borderRadius: "8px", padding: "0.55rem", fontSize: "0.85rem",
        fontFamily: "inherit", cursor: "pointer", fontWeight: 600,
      }}>{t("installModal.gotIt")}</button>
    </div>
  );
}

const NAV_IDS = ["ats", "doc", "linux", "mac", "resume", "windows", "workflow"];

export default function Header({ active, onSelect, enabledKeys }) {
  const { t } = useTranslation(["nav", "common"]);
  const { user, logout } = useAuth();
  const { canInstall, install, isInstalled, showLinuxTrustTip, dismissLinuxTrustTip } = usePWA();
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  // enabledKeys undefined means the entitlements check failed -- fail open
  // and show every tool rather than hide the whole nav over a transient error.
  const visibleNavIds = enabledKeys ? NAV_IDS.filter((id) => enabledKeys.has(id)) : NAV_IDS;

  function handleInstall() {
    if (canInstall) install();
    else setShowInstallModal(true);
  }

  function selectFromDrawer(id) {
    onSelect(id);
    setDrawerOpen(false);
  }

  useEffect(() => {
    if (!drawerOpen) return;
    document.body.style.overflow = "hidden";
    function onKeyDown(e) {
      if (e.key === "Escape") setDrawerOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [drawerOpen]);

  return (
    <header className="site-header">
      <button
        className="nav-toggle"
        aria-label={t("common:menu")}
        aria-expanded={drawerOpen}
        onClick={() => setDrawerOpen(true)}
      >
        <MenuIcon />
      </button>
      <div className="brand">
        <span className="brand-name">
          Torres<span className="brand-accent">Tech</span> Remote
        </span>
        <div className="brand-divider" />
        <span className="brand-product">Workblox</span>
      </div>
      <nav className="tool-nav">
        {visibleNavIds.map((id) => (
          <button
            key={id}
            className={active === id ? "active" : ""}
            onClick={() => onSelect(id)}
          >
            {t(`nav:${id}`)}
          </button>
        ))}
        <button
          className={active === "settings" ? "active" : ""}
          onClick={() => onSelect("settings")}
        >
          {t("nav:settings")}
        </button>
        {user?.isAdmin && (
          <button
            className={active === "admin" ? "active" : ""}
            onClick={() => onSelect("admin")}
          >
            {t("nav:admin")}
          </button>
        )}
      </nav>
      <div className="header-user">
        <span className="header-user-name">{user?.name}</span>
        <LanguageSwitcher />
        {!isInstalled && <button className="header-install" onClick={handleInstall}>⊕ {t("common:install")}</button>}
        <button className="header-signout" onClick={logout}>{t("common:signOut")}</button>
      </div>
      {showInstallModal && <InstallModal onClose={() => setShowInstallModal(false)} />}
      {showLinuxTrustTip && <LinuxTrustTip onClose={dismissLinuxTrustTip} />}

      <div className={`nav-drawer-overlay ${drawerOpen ? "open" : ""}`} onClick={() => setDrawerOpen(false)} />
      <div className={`nav-drawer ${drawerOpen ? "open" : ""}`} role="dialog" aria-modal="true" aria-hidden={!drawerOpen}>
        <div className="nav-drawer-header">
          <span className="brand-name" style={{ fontSize: "1rem" }}>
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <button className="nav-drawer-close" aria-label={t("common:closeMenu")} onClick={() => setDrawerOpen(false)}>
            ×
          </button>
        </div>
        <nav className="nav-drawer-list">
          {visibleNavIds.map((id) => (
            <button
              key={id}
              className={`nav-drawer-item ${active === id ? "active" : ""}`}
              onClick={() => selectFromDrawer(id)}
            >
              {t(`nav:${id}`)}
            </button>
          ))}
          <button
            className={`nav-drawer-item ${active === "settings" ? "active" : ""}`}
            onClick={() => selectFromDrawer("settings")}
          >
            {t("nav:settings")}
          </button>
          {user?.isAdmin && (
            <button
              className={`nav-drawer-item ${active === "admin" ? "active" : ""}`}
              onClick={() => selectFromDrawer("admin")}
            >
              {t("nav:admin")}
            </button>
          )}
        </nav>
        <div className="nav-drawer-divider" />
        <div className="nav-drawer-user">
          <span className="header-user-name">{user?.name}</span>
          <LanguageSwitcher />
          {!isInstalled && (
            <button className="header-install" onClick={() => { handleInstall(); setDrawerOpen(false); }}>
              ⊕ {t("common:install")}
            </button>
          )}
          <button className="header-signout" onClick={() => { logout(); setDrawerOpen(false); }}>
            {t("common:signOut")}
          </button>
        </div>
      </div>
    </header>
  );
}
