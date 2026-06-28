import { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import Login from "./components/auth/Login";
import SignUp from "./components/auth/SignUp";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import ATSAnalyzer from "./components/tools/ATSAnalyzer";
import DocAnalyzer from "./components/tools/DocAnalyzer";
import LinuxHelper from "./components/tools/LinuxHelper";
import MacHelper from "./components/tools/MacHelper";
import ResumeBuilder from "./components/tools/ResumeBuilder";
import WindowsHelper from "./components/tools/WindowsHelper";
import WorkflowBuilder from "./components/tools/WorkflowBuilder";

const TOOLS = {
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
  const [authView, setAuthView] = useState("login");
  const Tool = TOOLS[active];

  if (!user) {
    return authView === "signup"
      ? <SignUp onSwitchToLogin={() => setAuthView("login")} />
      : <Login onSwitchToSignUp={() => setAuthView("signup")} />;
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
