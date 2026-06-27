import { useState } from "react";
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
  const [active, setActive] = useState("doc");
  const Tool = TOOLS[active];

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
