import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

export default function PolicyGenerator() {
  const { loading, error, call } = useApi();
  const [policyType, setPolicyType] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [specifics, setSpecifics] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/policy", { policy_type: policyType, company_name: companyName, industry, specifics }));
    if (result) setData(result);
  }

  function copyAll() {
    if (!data) return;
    const lines = [
      data.title,
      `Effective: ${data.effective_date_placeholder}`,
      "",
      "Purpose",
      data.purpose,
      "",
      "Scope",
      data.scope,
      "",
      ...(data.sections || []).flatMap(s => [s.heading, s.content, ""]),
      data.acknowledgment_statement || "",
    ];
    navigator.clipboard.writeText(lines.join("\n"));
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Policy <span>Generator</span></h1>
      <p className="page-subtitle">Create professional company policies — HR, IT, remote work, PTO, and more.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Policy type (e.g. Remote Work Policy, PTO Policy) *" value={policyType} onChange={(e) => setPolicyType(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Company name" value={companyName} onChange={(e) => setCompanyName(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Industry (e.g. Technology, Healthcare)" value={industry} onChange={(e) => setIndustry(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder="Specific requirements or notes (optional)" value={specifics} onChange={(e) => setSpecifics(e.target.value)} rows={3} disabled={loading}
          style={{ ...inputStyle, resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Generating…" : "Generate Policy"}</button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Policy Document</p>
              <button className="copy-btn" onClick={copyAll}>Copy All</button>
            </div>
            <p style={{ fontWeight: 800, fontSize: "1.1rem", marginBottom: "0.25rem" }}>{data.title}</p>
            <p style={{ fontSize: "0.82rem", color: "var(--text-hint)" }}>Effective: {data.effective_date_placeholder}</p>
          </div>
          {data.purpose && (
            <div className="result-card">
              <p className="result-label">Purpose</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.purpose}</p>
            </div>
          )}
          {data.scope && (
            <div className="result-card">
              <p className="result-label">Scope</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.scope}</p>
            </div>
          )}
          {(data.sections || []).map((section, i) => (
            <div key={i} className="result-card">
              <p className="result-label">{section.heading}</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65, whiteSpace: "pre-wrap" }}>{section.content}</p>
            </div>
          ))}
          {data.acknowledgment_statement && (
            <div className="result-card">
              <p className="result-label">Acknowledgment</p>
              <p style={{ fontSize: "0.88rem", lineHeight: 1.6, fontStyle: "italic" }}>{data.acknowledgment_statement}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
