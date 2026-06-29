import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

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
    const result = await call(() => post("/api/biz/job-desc", {
      job_title: jobTitle,
      department,
      requirements,
      salary_range: salaryRange,
      company_info: companyInfo,
    }));
    if (result) setData(result);
  }

  function copyAll() {
    if (!data) return;
    const lines = [
      `# ${data.job_title}`,
      "",
      data.overview,
      "",
      "## Responsibilities",
      ...(data.responsibilities || []).map(r => `- ${r}`),
      "",
      "## Requirements",
      ...(data.requirements || []).map(r => `- ${r}`),
      "",
      "## Nice to Have",
      ...(data.nice_to_have || []).map(r => `- ${r}`),
      "",
      "## Benefits",
      ...(data.benefits || []).map(r => `- ${r}`),
    ];
    navigator.clipboard.writeText(lines.join("\n"));
  }

  return (
    <div>
      <h1 className="page-title">Job Description <span>Writer</span></h1>
      <p className="page-subtitle">Create a compelling, complete job description that attracts top talent.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Job title *" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} required disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <input type="text" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <input type="text" placeholder="Salary range (e.g. $60k–$80k)" value={salaryRange} onChange={(e) => setSalaryRange(e.target.value)} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <textarea placeholder="Key requirements and responsibilities *" value={requirements} onChange={(e) => setRequirements(e.target.value)} rows={3} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }} />
        <textarea placeholder="Brief company description (optional)" value={companyInfo} onChange={(e) => setCompanyInfo(e.target.value)} rows={2} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Writing…" : "Write Job Description"}</button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Overview</p>
              <button className="copy-btn" onClick={copyAll}>Copy All</button>
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
        </>
      )}
    </div>
  );
}
