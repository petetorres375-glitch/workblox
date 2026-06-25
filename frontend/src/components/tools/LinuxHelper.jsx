import { useState } from "react";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";

export default function LinuxHelper() {
  const [problem, setProblem] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const { loading, error, call } = useApi();

  async function handleSubmit(e) {
    e.preventDefault();
    const data = await call(() => post("/api/linux", { problem }));
    if (data) setResult(data);
  }

  function copy() {
    navigator.clipboard.writeText(result.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <h1 className="page-title">Linux <span>Helper</span></h1>
      <p className="page-subtitle">Describe a Linux problem in plain English — get the command back.</p>

      <form onSubmit={handleSubmit}>
        <div className="search-box">
          <input
            type="text"
            placeholder="e.g. find all .log files modified in the last 7 days"
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
