import { useState } from "react";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import DocAnalyzer from "./components/tools/DocAnalyzer";
import LinuxHelper from "./components/tools/LinuxHelper";
import MacHelper from "./components/tools/MacHelper";
import WindowsHelper from "./components/tools/WindowsHelper";
import WorkflowBuilder from "./components/tools/WorkflowBuilder";

const TOOL_TITLES = {
  doc: "Doc Analyzer",
  workflow: "Workflow Builder",
  linux: "Linux Helper",
  windows: "Windows Helper",
  mac: "Mac Helper",
};

const TOOLS = {
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
    <div className="layout">
      <Sidebar active={active} onSelect={setActive} />
      <div className="main-content">
        <Header title={TOOL_TITLES[active]} />
        <Tool />
        <Footer />
      </div>
    </div>
  );
}
