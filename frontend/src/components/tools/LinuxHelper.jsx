import { useState } from "react";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";
import Button from "../ui/Button";
import ErrorBanner from "../ui/ErrorBanner";
import Spinner from "../ui/Spinner";

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
    <div className="tool-area">
      <h2>Linux Helper</h2>
      <p className="subtitle">Describe a Linux problem in plain English — get the command back.</p>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="linux-problem">Problem</label>
          <textarea
            id="linux-problem"
            className="input"
            rows={3}
            placeholder="e.g. find all .log files modified in the last 7 days"
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={loading || !problem.trim()}>
          {loading ? "Thinking..." : "Get Command"}
        </Button>
      </form>

      {loading && <Spinner />}
      <ErrorBanner message={error} />

      {result && !loading && (
        <div className="result-block">
          <div className="result-header">
            <h3>Command</h3>
            <button className="copy-btn" onClick={copy}>{copied ? "Copied!" : "Copy"}</button>
          </div>
          <div className="command-box">{result.command}</div>

          <h3 style={{ marginTop: 16 }}>Explanation</h3>
          <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{result.explanation}</p>

          {result.warnings && result.warnings[0] !== "None." && (
            <>
              <h3 style={{ marginTop: 16 }}>Warnings</h3>
              <ul className="warning-list">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
