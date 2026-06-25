import { useState } from "react";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";
import Button from "../ui/Button";
import ErrorBanner from "../ui/ErrorBanner";
import Spinner from "../ui/Spinner";

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
    <div className="tool-area">
      <h2>Workflow Builder</h2>
      <p className="subtitle">Describe a repetitive task — get a ready-to-run Python script.</p>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="workflow-task">Task</label>
          <textarea
            id="workflow-task"
            className="input"
            rows={3}
            placeholder="e.g. rename all photos in a folder by their date taken"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={loading || !task.trim()}>
          {loading ? "Generating..." : "Build Script"}
        </Button>
      </form>

      {loading && <Spinner />}
      <ErrorBanner message={error} />

      {result && !loading && (
        <div className="result-block">
          <div className="result-header">
            <h3>{result.filename}</h3>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="copy-btn" onClick={copy}>{copied ? "Copied!" : "Copy"}</button>
              <button className="copy-btn" onClick={download}>Download</button>
            </div>
          </div>
          <pre className="script-box">{result.script}</pre>
        </div>
      )}
    </div>
  );
}
