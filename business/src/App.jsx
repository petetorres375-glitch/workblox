import { useEffect, useState } from "react";
import { get } from "./api/client";
import { useAuth } from "./contexts/AuthContext";
import Login from "./components/auth/Login";
import SignUp from "./components/auth/SignUp";
import Welcome from "./components/auth/Welcome";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import AccountSettings from "./components/tools/AccountSettings";
import AdCopyWriter from "./components/tools/AdCopyWriter";
import Contacts from "./components/tools/Contacts";
import BatchATSAnalyzer from "./components/tools/BatchATSAnalyzer";
import BusinessEmailDrafter from "./components/tools/BusinessEmailDrafter";
import ContractAnalyzer from "./components/tools/ContractAnalyzer";
import CustomerResponseDrafter from "./components/tools/CustomerResponseDrafter";
import HiringManager from "./components/tools/HiringManager";
import JobDescWriter from "./components/tools/JobDescWriter";
import MeetingNotesCleaner from "./components/tools/MeetingNotesCleaner";
import PolicyGenerator from "./components/tools/PolicyGenerator";
import ProposalGenerator from "./components/tools/ProposalGenerator";
import ReviewRequestEmail from "./components/tools/ReviewRequestEmail";
import SOPGenerator from "./components/tools/SOPGenerator";
import SocialMediaGenerator from "./components/tools/SocialMediaGenerator";
import ToolPicker from "./components/tools/ToolPicker";

const TOOLS = {
  hiring: HiringManager,
  "batch-ats": BatchATSAnalyzer,
  "job-desc": JobDescWriter,
  proposal: ProposalGenerator,
  contract: ContractAnalyzer,
  customer: CustomerResponseDrafter,
  review: ReviewRequestEmail,
  social: SocialMediaGenerator,
  "ad-copy": AdCopyWriter,
  policy: PolicyGenerator,
  sop: SOPGenerator,
  meeting: MeetingNotesCleaner,
  email: BusinessEmailDrafter,
  contacts: Contacts,
};

export default function App() {
  const { user, logout, planBlocked } = useAuth();
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
    get("/api/entitlements")
      .then((data) => {
        if (cancelled) return;
        const keys = new Set(data.tool_keys);
        setEnabledKeys(keys);
        setActive((current) => (current && keys.has(current) ? current : [...keys][0] ?? null));
      })
      .catch(() => {
        if (!cancelled) setEnabledKeys(undefined);
      });
    return () => { cancelled = true; };
  }, [user, entered, refreshKey]);

  if (!user) {
    if (planBlocked) {
      return (
        <div className="login-page">
          <div className="login-card">
            <div className="login-brand">
              <span className="brand-name" style={{ fontSize: "1.1rem" }}>
                Torres<span className="brand-accent">Tech</span> Remote
              </span>
              <span className="login-product">Workblox Business</span>
            </div>
            <p className="login-error" style={{ marginTop: "1.5rem" }}>
              Business subscription required.
            </p>
            <p className="page-subtitle" style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
              Contact{" "}
              <a href="mailto:pedro_torres@torrestechremote.com" style={{ color: "var(--orange)", fontWeight: 600 }}>
                Torres Tech Remote
              </a>{" "}
              to upgrade your account.
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

  const Tool = TOOLS[active] || HiringManager;

  return (
    <>
      <Header active={active} onSelect={setActive} enabledKeys={enabledKeys} />
      <main>
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
