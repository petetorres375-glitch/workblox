import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data) {
  const lines = [`JOB DESCRIPTION — ${(data.job_title || "").toUpperCase()}`, "=".repeat(60), "", data.overview || "", ""];
  lines.push("RESPONSIBILITIES", "-".repeat(40));
  (data.responsibilities || []).forEach((r, i) => lines.push(`${i + 1}. ${r}`));
  lines.push("", "REQUIREMENTS", "-".repeat(40));
  (data.requirements || []).forEach((r, i) => lines.push(`${i + 1}. ${r}`));
  if (data.nice_to_have?.length) {
    lines.push("", "NICE TO HAVE", "-".repeat(40));
    data.nice_to_have.forEach((r, i) => lines.push(`${i + 1}. ${r}`));
  }
  if (data.benefits?.length) {
    lines.push("", "BENEFITS", "-".repeat(40));
    data.benefits.forEach((r, i) => lines.push(`${i + 1}. ${r}`));
  }
  if (data.about_company_placeholder) {
    lines.push("", "ABOUT THE COMPANY", "-".repeat(40), data.about_company_placeholder);
  }
  return lines.join("\n");
}

function buildMd(data) {
  const lines = [`# ${data.job_title || "Job Description"}`, "", data.overview || "", ""];
  lines.push("## Responsibilities");
  (data.responsibilities || []).forEach((r) => lines.push(`- ${r}`));
  lines.push("", "## Requirements");
  (data.requirements || []).forEach((r) => lines.push(`- ${r}`));
  if (data.nice_to_have?.length) { lines.push("", "## Nice to Have"); data.nice_to_have.forEach((r) => lines.push(`- ${r}`)); }
  if (data.benefits?.length) { lines.push("", "## Benefits"); data.benefits.forEach((r) => lines.push(`- ${r}`)); }
  if (data.about_company_placeholder) { lines.push("", "## About the Company", data.about_company_placeholder); }
  return lines.join("\n");
}

export default function JobDescWriter() {
  const { loading, error, call } = useApi();
  const [jobTitle, setJobTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [requirements, setRequirements] = useState("");
  const [salaryRange, setSalaryRange] = useState("");
  const [companyInfo, setCompanyInfo] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/job-desc", { job_title: jobTitle, department, requirements, salary_range: salaryRange, company_info: companyInfo }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Job Description <span>Writer</span></h1>
      <p className="page-subtitle">Create a compelling, complete job description that attracts top talent.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Job title *" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Salary range (e.g. $60k–$80k)" value={salaryRange} onChange={(e) => setSalaryRange(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder="Key requirements and responsibilities *" value={requirements} onChange={(e) => setRequirements(e.target.value)} rows={3} disabled={loading}
          style={{ ...inputStyle, resize: "vertical" }} />
        <textarea placeholder="Brief company description (optional)" value={companyInfo} onChange={(e) => setCompanyInfo(e.target.value)} rows={2} disabled={loading}
          style={{ ...inputStyle, resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Writing…" : "Write Job Description"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{data.job_title}</strong></div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Overview</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(buildMd(data))}>Copy All</button>
            </div>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65, fontWeight: 700, marginBottom: "0.5rem" }}>{data.job_title}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.overview}</p>
          </div>
          {[["Responsibilities", data.responsibilities], ["Requirements", data.requirements], ["Nice to Have", data.nice_to_have], ["Benefits", data.benefits]].map(([label, items]) =>
            items?.length > 0 && (
              <div className="result-card" key={label}>
                <p className="result-label">{label}</p>
                <ul className="section-list">{items.map((item, i) => <li key={i}>{item}</li>)}</ul>
              </div>
            )
          )}
          <ReportToolbar
            filename={slug(jobTitle) || "job_description"}
            subject={`Job Description — ${data.job_title || jobTitle}`}
            txtContent={buildTxt(data)}
            mdContent={buildMd(data)}
          />
        </>
      )}
    </div>
  );
}
