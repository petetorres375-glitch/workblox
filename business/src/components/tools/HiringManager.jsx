import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

export default function HiringManager() {
  const { loading, error, call } = useApi();
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [requirements, setRequirements] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/hiring-manager", {
      job_title: jobTitle,
      department,
      requirements,
    }));
    if (result) setData(result);
  }

  function copyText(text) {
    navigator.clipboard.writeText(Array.isArray(text) ? text.join("\n") : text);
  }

  return (
    <div>
      <h1 className="page-title">Hiring <span>Manager</span></h1>
      <p className="page-subtitle">Generate interview questions, evaluation criteria, and a hiring package for any role.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input
          type="text"
          placeholder="Job title (e.g. Senior Software Engineer)"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          required
          disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }}
        />
        <input
          type="text"
          placeholder="Department (e.g. Engineering)"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }}
        />
        <textarea
          placeholder="Key requirements and responsibilities..."
          value={requirements}
          onChange={(e) => setRequirements(e.target.value)}
          rows={4}
          disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }}
        />
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Generating…" : "Generate Hiring Package"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Position Summary</p>
            </div>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.position_summary}</p>
          </div>

          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Interview Questions</p>
              <button className="copy-btn" onClick={() => copyText(data.interview_questions)}>Copy</button>
            </div>
            <ul className="section-list">
              {(data.interview_questions || []).map((q, i) => <li key={i}>{q}</li>)}
            </ul>
          </div>

          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Evaluation Criteria</p>
              <button className="copy-btn" onClick={() => copyText(data.evaluation_criteria)}>Copy</button>
            </div>
            <ul className="section-list">
              {(data.evaluation_criteria || []).map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>

          {data.red_flags?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Red Flags to Watch</p>
              <ul className="warning-list">
                {data.red_flags.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}

          {data.onboarding_tips?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Onboarding Tips</p>
              <ul className="section-list">
                {data.onboarding_tips.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
