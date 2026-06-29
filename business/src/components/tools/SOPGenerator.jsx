import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

export default function SOPGenerator() {
  const { loading, error, call } = useApi();
  const [processName, setProcessName] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [frequency, setFrequency] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/sop", { process_name: processName, department, description, frequency }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">SOP <span>Generator</span></h1>
      <p className="page-subtitle">Create clear, actionable Standard Operating Procedures for any business process.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Process name (e.g. Customer Onboarding) *" value={processName} onChange={(e) => setProcessName(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Frequency (e.g. Daily, Weekly, Per new client)" value={frequency} onChange={(e) => setFrequency(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder="Description of the process *" value={description} onChange={(e) => setDescription(e.target.value)} required rows={3} disabled={loading}
          style={{ ...inputStyle, resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Generating…" : "Generate SOP"}</button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          <div className="result-card">
            <p className="result-label">Overview</p>
            <p style={{ fontWeight: 800, fontSize: "1.05rem", marginBottom: "0.4rem" }}>{data.title}</p>
            <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>Frequency: {data.frequency}</p>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.purpose}</p>
          </div>
          {data.required_tools?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Required Tools / Resources</p>
              <ul className="section-list">{data.required_tools.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          {data.steps?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Steps</p>
              {data.steps.map((step, i) => (
                <div key={i} style={{ marginBottom: "1rem", paddingLeft: "1rem", borderLeft: "3px solid var(--orange)" }}>
                  <p style={{ fontWeight: 700, marginBottom: "0.2rem" }}>Step {step.step_number}: {step.action}</p>
                  <p style={{ fontSize: "0.9rem", lineHeight: 1.6, color: "var(--text-muted)" }}>{step.details}</p>
                  {step.warning && (
                    <p style={{ fontSize: "0.82rem", color: "#b45309", marginTop: "0.25rem" }}>⚠ {step.warning}</p>
                  )}
                </div>
              ))}
            </div>
          )}
          {data.quality_checks?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Quality Checks</p>
              <ul className="section-list">{data.quality_checks.map((q, i) => <li key={i}>{q}</li>)}</ul>
            </div>
          )}
          {data.notes && (
            <div className="result-card">
              <p className="result-label">Notes</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.notes}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
