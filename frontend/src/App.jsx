import { useState } from "react";
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
  const [authView, setAuthView] = useState("welcome");
  const Tool = TOOLS[active] || ATSAnalyzer;

  if (!user) {
    if (authView === "welcome") {
      return <Welcome onEnter={() => setAuthView("login")} />;
    }
    return authView === "signup"
      ? <SignUp onSwitchToLogin={() => setAuthView("login")} onBack={() => setAuthView("welcome")} />
      : <Login onSwitchToSignUp={() => setAuthView("signup")} onBack={() => setAuthView("welcome")} />;
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
