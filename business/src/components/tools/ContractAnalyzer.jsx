import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { postForm } from "../../api/client";

const RISK_COLOR = { low: "#16a34a", medium: "#b45309", high: "#dc2626" };

export default function ContractAnalyzer() {
  const { loading, error, call } = useApi();
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [data, setData] = useState(null);

  function handleFile(f) {
    if (f) { setFile(f); setData(null); }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const result = await call(() => postForm("/api/biz/contract", fd));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title">Contract <span>Analyzer</span></h1>
      <p className="page-subtitle">Upload a contract and get a plain-language summary, risk assessment, and key clauses.</p>

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone${dragOver ? " active" : ""}${file ? " active" : ""}`}
          onClick={() => document.getElementById("contract-file").click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
        >
          <input id="contract-file" type="file" accept=".pdf,.txt,.docx,.doc" onChange={(e) => handleFile(e.target.files[0])} />
          <p className="drop-label">{file ? file.name : "Drop contract here or click to browse"}</p>
          <p className="drop-hint">PDF, DOCX, or TXT</p>
        </div>
        <button type="submit" className="submit-btn" disabled={loading || !file}>
          {loading ? "Analyzing…" : "Analyze Contract"}
        </button>
      </form>

      {error && <div className="error-banner" style={{ marginTop: "1rem" }}>{error}</div>}

      {data && (
        <>
          <div className="result-card" style={{ marginTop: "1.5rem" }}>
            <div className="result-header">
              <p className="result-label">Document Overview</p>
              {data.overall_risk && (
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: RISK_COLOR[data.overall_risk] || "#666", textTransform: "uppercase" }}>
                  {data.overall_risk} risk
                </span>
              )}
            </div>
            <p style={{ fontWeight: 700, marginBottom: "0.4rem" }}>{data.document_type}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.summary}</p>
          </div>

          {data.key_obligations?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Key Obligations</p>
              <ul className="section-list">{data.key_obligations.map((o, i) => <li key={i}>{o}</li>)}</ul>
            </div>
          )}

          {data.payment_terms && (
            <div className="result-card">
              <p className="result-label">Payment Terms</p>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.payment_terms}</p>
            </div>
          )}

          {data.red_flags?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Red Flags</p>
              <ul className="warning-list">{data.red_flags.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}

          {data.missing_standard_clauses?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Missing Standard Clauses</p>
              <ul className="warning-list">{data.missing_standard_clauses.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </div>
          )}

          {data.recommendation && (
            <div className="result-card">
              <p className="result-label">Recommendation</p>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.recommendation}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
