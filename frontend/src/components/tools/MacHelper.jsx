import { useState } from "react";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";

export default function MacHelper() {
  const [problem, setProblem] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const { loading, error, call } = useApi();

  async function handleSubmit(e) {
    e.preventDefault();
    const data = await call(() => post("/api/mac", { problem }));
    if (data) setResult(data);
  }

  function copy() {
    navigator.clipboard.writeText(result.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <h1 className="page-title">Mac <span>Helper</span></h1>
      <p className="page-subtitle">Describe a macOS problem in plain English — get the Terminal command back.</p>

      <form onSubmit={handleSubmit}>
        <div className="search-box">
          <input
            type="text"
            placeholder="e.g. show disk usage for each folder in my home directory"
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
          />
          <button type="submit" disabled={loading || !problem.trim()}>
            {loading ? "Thinking..." : "Ask"}
          </button>
        </div>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {result && !loading && (
        <>
          {result.gui_steps?.length > 0 && result.gui_steps[0] !== "No GUI method available for this task." && (
            <div className="result-card">
              <div className="result-label">GUI Steps</div>
              <ol className="warning-list" style={{ paddingLeft: "1.2rem" }}>
                {result.gui_steps.map((s, i) => <li key={i} style={{ marginBottom: "0.4rem" }}>{s}</li>)}
              </ol>
            </div>
          )}

          <div className="result-card">
            <div className="result-header">
              <div className="result-label">Command</div>
              <button className="copy-btn" onClick={copy}>{copied ? "Copied!" : "Copy"}</button>
            </div>
            <div className="command-box">{result.command}</div>
          </div>

          <div className="result-card">
            <div className="result-label">Explanation</div>
            <p className="explanation-text">{result.explanation}</p>
          </div>

          {result.warnings?.length > 0 && result.warnings[0] !== "None." && (
            <div className="result-card">
              <div className="result-label">Warnings</div>
              <ul className="warning-list">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </>
      )}
    </>
  );
}
