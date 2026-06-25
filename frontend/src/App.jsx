import { useState } from "react";
import Footer from "./components/layout/Footer";
import Header from "./components/layout/Header";
import DocAnalyzer from "./components/tools/DocAnalyzer";
import LinuxHelper from "./components/tools/LinuxHelper";
import MacHelper from "./components/tools/MacHelper";
import WindowsHelper from "./components/tools/WindowsHelper";
import WorkflowBuilder from "./components/tools/WorkflowBuilder";

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
    <>
      <Header active={active} onSelect={setActive} />
      <main>
        <Tool />
      </main>
      <Footer />
    </>
  );
}
