import { useEffect, useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import Login from "./components/auth/Login";
import SignUp from "./components/auth/SignUp";
import Welcome from "./components/auth/Welcome";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import Admin from "./components/tools/Admin";
import ATSAnalyzer from "./components/tools/ATSAnalyzer";
import DocAnalyzer from "./components/tools/DocAnalyzer";
import LinuxHelper from "./components/tools/LinuxHelper";
import MacHelper from "./components/tools/MacHelper";
import ResumeBuilder from "./components/tools/ResumeBuilder";
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
  const { user } = useAuth();
  const [active, setActive] = useState("ats");
  const [entered, setEntered] = useState(false);
  // Sign-up has no visible link anywhere in the app -- it's only reachable
  // via a direct ?signup URL Pedro can hand to a new client, since existing
  // clients only ever need Login.
  const [authView, setAuthView] = useState(() =>
    new URLSearchParams(window.location.search).has("signup") ? "signup" : "login"
  );
  const Tool = TOOLS[active] || ATSAnalyzer;

  useEffect(() => {
    if (!user) setEntered(false);
  }, [user]);

  useEffect(() => {
    if (authView === "signup" && window.location.search.includes("signup")) {
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [authView]);

  if (!user) {
    return authView === "signup"
      ? <SignUp onSwitchToLogin={() => setAuthView("login")} />
      : <Login />;
  }

  if (!entered) {
    return <Welcome onEnter={() => setEntered(true)} />;
  }

  return (
    <>
      <Header active={active} onSelect={setActive} />
      <main>
        <Tool />
      </main>
      <Footer />
    </>
  );
}
