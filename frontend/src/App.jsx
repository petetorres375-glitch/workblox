import { useEffect, useState } from "react";
import { get } from "./api/client";
import { useAuth } from "./contexts/AuthContext";
import Login from "./components/auth/Login";
import SignUp from "./components/auth/SignUp";
import Welcome from "./components/auth/Welcome";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import AccountSettings from "./components/tools/AccountSettings";
import Admin from "./components/tools/Admin";
import ATSAnalyzer from "./components/tools/ATSAnalyzer";
import DocAnalyzer from "./components/tools/DocAnalyzer";
import LinuxHelper from "./components/tools/LinuxHelper";
import MacHelper from "./components/tools/MacHelper";
import ResumeBuilder from "./components/tools/ResumeBuilder";
import ToolPicker from "./components/tools/ToolPicker";
import WindowsHelper from "./components/tools/WindowsHelper";
import WorkflowBuilder from "./components/tools/WorkflowBuilder";

const TOOLS = {
  admin: Admin,
  resume: ResumeBuilder,
  ats: ATSAnalyzer,
  doc: DocAnalyzer,
  workflow: WorkflowBuilder,
  linux: LinuxHelper,
  windows: WindowsHelper,
  mac: MacHelper,
};

export default function App() {
  const { user, logout, accessBlocked } = useAuth();
  const [active, setActive] = useState(null);
  const [entered, setEntered] = useState(false);
  // null = still checking; a Set = the user's real enabled tool keys;
  // undefined = the check failed, so fail open and show every tool rather
  // than lock an existing user out over a transient API error.
  const [enabledKeys, setEnabledKeys] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  // Sign-up has no visible link anywhere in the app -- it's only reachable
  // via a direct ?signup URL Pedro can hand to a new client, since existing
  // clients only ever need Login.
  const [authView, setAuthView] = useState(() =>
    new URLSearchParams(window.location.search).has("signup") ? "signup" : "login"
  );

  useEffect(() => {
    if (!user) {
      setEntered(false);
      setEnabledKeys(null);
      setActive(null);
    }
  }, [user]);

  useEffect(() => {
    if (authView === "signup" && window.location.search.includes("signup")) {
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [authView]);

  useEffect(() => {
    if (!user || !entered) return;
    let cancelled = false;
    get("/api/entitlements?app=personal")
      .then((data) => {
        if (cancelled) return;
        const keys = new Set(data.tool_keys);
        setEnabledKeys(keys);
        setActive((current) => {
          // "settings" and "admin" aren't tool keys -- they're always
          // available regardless of entitlements, so a refresh (e.g. right
          // after saving in Settings) must never bounce the user away from
          // them the way it would for a tool they just deselected.
          if (current === "settings" || current === "admin") return current;
          return current && keys.has(current) ? current : [...keys][0] ?? null;
        });
      })
      .catch(() => {
        if (!cancelled) setEnabledKeys(undefined);
      });
    return () => { cancelled = true; };
  }, [user, entered, refreshKey]);

  if (!user) {
    if (accessBlocked) {
      return (
        <div className="login-page">
          <div className="login-card">
            <div className="login-brand">
              <span className="brand-name" style={{ fontSize: "1.1rem" }}>
                Torres<span className="brand-accent">Tech</span> Remote
              </span>
              <span className="login-product">Workblox</span>
            </div>
            <p className="login-error" style={{ marginTop: "1.5rem" }}>
              Personal access required.
            </p>
            <p className="page-subtitle" style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              Contact{" "}
              <a href="mailto:pedro_torres@torrestechremote.com" style={{ color: "var(--orange)", fontWeight: 600 }}>
                Torres Tech Remote
              </a>{" "}
              to activate your account.
            </p>
            <button className="auth-link" onClick={logout} style={{ marginTop: "1.25rem" }}>
              Sign out
            </button>
          </div>
        </div>
      );
    }
    return authView === "signup"
      ? <SignUp onSwitchToLogin={() => setAuthView("login")} />
      : <Login />;
  }

  if (!entered) {
    return <Welcome onEnter={() => setEntered(true)} />;
  }

  if (enabledKeys === null) {
    return null; // still checking -- avoid a flash of the wrong screen
  }

  if (enabledKeys instanceof Set && enabledKeys.size === 0) {
    return <ToolPicker variant="signup" onDone={() => setRefreshKey((k) => k + 1)} />;
  }

  const Tool = TOOLS[active] || ATSAnalyzer;

  return (
    <>
      <Header active={active} onSelect={setActive} enabledKeys={enabledKeys} />
      <main className={active === "admin" ? "main-wide" : undefined}>
        {active === "settings" ? (
          <AccountSettings onSaved={() => setRefreshKey((k) => k + 1)} />
        ) : (
          <Tool />
        )}
      </main>
      <Footer />
    </>
  );
}
