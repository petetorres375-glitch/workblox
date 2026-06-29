import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, jobTitle, department) {
  const title = department ? `${jobTitle} — ${department}` : jobTitle;
  const lines = [`HIRING PACKAGE — ${title.toUpperCase()}`, "=".repeat(60), ""];
  lines.push("POSITION SUMMARY", "-".repeat(40), data.position_summary || "", "");
  lines.push("INTERVIEW QUESTIONS", "-".repeat(40));
  (data.interview_questions || []).forEach((q, i) => lines.push(`${i + 1}. ${q}`));
  lines.push("", "EVALUATION CRITERIA", "-".repeat(40));
  (data.evaluation_criteria || []).forEach((c, i) => lines.push(`${i + 1}. ${c}`));
  if (data.red_flags?.length) {
    lines.push("", "RED FLAGS TO WATCH", "-".repeat(40));
    data.red_flags.forEach((f, i) => lines.push(`${i + 1}. ${f}`));
  }
  if (data.onboarding_tips?.length) {
    lines.push("", "ONBOARDING TIPS", "-".repeat(40));
    data.onboarding_tips.forEach((t, i) => lines.push(`${i + 1}. ${t}`));
  }
  return lines.join("\n");
}

function buildMd(data, jobTitle, department) {
  const title = department ? `${jobTitle} — ${department}` : jobTitle;
  const lines = [`# Hiring Package — ${title}`, "", "## Position Summary", data.position_summary || "", ""];
  lines.push("## Interview Questions");
  (data.interview_questions || []).forEach((q) => lines.push(`- ${q}`));
  lines.push("", "## Evaluation Criteria");
  (data.evaluation_criteria || []).forEach((c) => lines.push(`- ${c}`));
  if (data.red_flags?.length) {
    lines.push("", "## Red Flags to Watch");
    data.red_flags.forEach((f) => lines.push(`- ${f}`));
  }
  if (data.onboarding_tips?.length) {
    lines.push("", "## Onboarding Tips");
    data.onboarding_tips.forEach((t) => lines.push(`- ${t}`));
  }
  return lines.join("\n");
}

export default function HiringManager() {
  const { loading, error, call } = useApi();
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [requirements, setRequirements] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setData(null);
    const result = await call(() => post("/api/biz/hiring-manager", { job_title: jobTitle, department, requirements }));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title">Hiring <span>Manager</span></h1>
      <p className="page-subtitle">Generate interview questions, evaluation criteria, and a hiring package for any role.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Job title (e.g. Senior Software Engineer)" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <input type="text" placeholder="Department (e.g. Engineering)" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <textarea placeholder="Key requirements and responsibilities..." value={requirements} onChange={(e) => setRequirements(e.target.value)} rows={4} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Generating…" : "Generate Hiring Package"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}>
            <strong>Hiring Package — {jobTitle}{department ? ` (${department})` : ""}</strong>
          </div>
          <div className="result-card">
            <p className="result-label">Position Summary</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.position_summary}</p>
          </div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Interview Questions</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText((data.interview_questions || []).join("\n"))}>Copy</button>
            </div>
            <ul className="section-list">{(data.interview_questions || []).map((q, i) => <li key={i}>{q}</li>)}</ul>
          </div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Evaluation Criteria</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText((data.evaluation_criteria || []).join("\n"))}>Copy</button>
            </div>
            <ul className="section-list">{(data.evaluation_criteria || []).map((c, i) => <li key={i}>{c}</li>)}</ul>
          </div>
          {data.red_flags?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Red Flags to Watch</p>
              <ul className="warning-list">{data.red_flags.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}
          {data.onboarding_tips?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Onboarding Tips</p>
              <ul className="section-list">{data.onboarding_tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          <ReportToolbar
            filename={slug(jobTitle) || "hiring_package"}
            subject={`Hiring Package — ${jobTitle}${department ? ` (${department})` : ""}`}
            txtContent={buildTxt(data, jobTitle, department)}
            mdContent={buildMd(data, jobTitle, department)}
          />
        </>
      )}
    </div>
  );
}
