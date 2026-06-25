import { useState } from "react";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";

export default function WorkflowBuilder() {
  const [task, setTask] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const { loading, error, call } = useApi();

  async function handleSubmit(e) {
    e.preventDefault();
    const data = await call(() => post("/api/workflow", { task }));
    if (data) setResult(data);
  }

  function copy() {
    navigator.clipboard.writeText(result.script);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  function download() {
    const blob = new Blob([result.script], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = result.filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <h1 className="page-title">Workflow <span>Builder</span></h1>
      <p className="page-subtitle">Describe a repetitive task — get a ready-to-run Python script.</p>

      <form onSubmit={handleSubmit}>
        <div className="search-box">
          <input
            type="text"
            placeholder="e.g. rename all photos in a folder by their date taken"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
          <button type="submit" disabled={loading || !task.trim()}>
            {loading ? "Building..." : "Build"}
          </button>
        </div>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {result && !loading && (
        <div className="result-card">
          <div className="result-header">
            <div className="result-label">{result.filename}</div>
            <div style={{ display: "flex", gap: 6 }}>
              <button className="copy-btn" onClick={copy}>{copied ? "Copied!" : "Copy"}</button>
              <button className="copy-btn" onClick={download}>Download</button>
            </div>
          </div>
          <pre className="script-box">{result.script}</pre>
        </div>
      )}
    </>
  );
}
