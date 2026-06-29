import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { postForm } from "../../api/client";
import ReportToolbar from "../ui/ReportToolbar";

const RISK_COLOR = { low: "#16a34a", medium: "#b45309", high: "#dc2626" };

function buildTxt(data, fileName) {
  const lines = [`CONTRACT ANALYSIS — ${(data.document_type || fileName || "Document").toUpperCase()}`, "=".repeat(60)];
  if (data.overall_risk) lines.push(`Overall Risk: ${data.overall_risk.toUpperCase()}`);
  lines.push("", "SUMMARY", "-".repeat(40), data.summary || "");
  if (data.key_obligations?.length) {
    lines.push("", "KEY OBLIGATIONS", "-".repeat(40));
    data.key_obligations.forEach((o, i) => lines.push(`${i + 1}. ${o}`));
  }
  if (data.payment_terms) lines.push("", "PAYMENT TERMS", "-".repeat(40), data.payment_terms);
  if (data.red_flags?.length) {
    lines.push("", "RED FLAGS", "-".repeat(40));
    data.red_flags.forEach((f, i) => lines.push(`${i + 1}. ${f}`));
  }
  if (data.missing_standard_clauses?.length) {
    lines.push("", "MISSING STANDARD CLAUSES", "-".repeat(40));
    data.missing_standard_clauses.forEach((c, i) => lines.push(`${i + 1}. ${c}`));
  }
  if (data.recommendation) lines.push("", "RECOMMENDATION", "-".repeat(40), data.recommendation);
  return lines.join("\n");
}

function buildMd(data, fileName) {
  const title = data.document_type || fileName || "Document";
  const lines = [`# Contract Analysis — ${title}`];
  if (data.overall_risk) lines.push(``, `**Overall Risk: ${data.overall_risk.toUpperCase()}**`);
  lines.push("", "## Summary", data.summary || "");
  if (data.key_obligations?.length) { lines.push("", "## Key Obligations"); data.key_obligations.forEach((o) => lines.push(`- ${o}`)); }
  if (data.payment_terms) lines.push("", "## Payment Terms", data.payment_terms);
  if (data.red_flags?.length) { lines.push("", "## Red Flags"); data.red_flags.forEach((f) => lines.push(`- ${f}`)); }
  if (data.missing_standard_clauses?.length) { lines.push("", "## Missing Standard Clauses"); data.missing_standard_clauses.forEach((c) => lines.push(`- ${c}`)); }
  if (data.recommendation) lines.push("", "## Recommendation", data.recommendation);
  return lines.join("\n");
}

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

  const baseName = file ? file.name.replace(/\.[^.]+$/, "") : "contract";

  return (
    <div>
      <h1 className="page-title">Contract <span>Analyzer</span></h1>
      <p className="page-subtitle">Upload a contract and get a plain-language summary, risk assessment, and key clauses.</p>

      <form onSubmit={handleSubmit} className="no-print">
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
        <button type="submit" className="submit-btn" disabled={loading || !file}>{loading ? "Analyzing…" : "Analyze Contract"}</button>
      </form>

      {error && <div className="error-banner no-print" style={{ marginTop: "1rem" }}>{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Contract Analysis — {data.document_type || baseName}</strong></div>
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
          <ReportToolbar
            filename={`${baseName}_analysis`}
            subject={`Contract Analysis — ${data.document_type || baseName}`}
            txtContent={buildTxt(data, baseName)}
            mdContent={buildMd(data, baseName)}
          />
        </>
      )}
    </div>
  );
}
