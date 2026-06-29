import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { postForm } from "../../api/client";

const LEVEL_COLOR = { Strong: "#16a34a", Good: "#2563eb", Fair: "#b45309", Weak: "#dc2626" };
const REC_COLOR = { Advance: "#16a34a", Maybe: "#b45309", Pass: "#dc2626" };

export default function BatchATSAnalyzer() {
  const { loading, error, call } = useApi();
  const [files, setFiles] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [data, setData] = useState(null);

  function handleFiles(fileList) {
    setFiles(Array.from(fileList).slice(0, 10));
    setData(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!files.length) return;
    const fd = new FormData();
    files.forEach(f => fd.append("resumes", f));
    fd.append("job_description", jobDescription);
    const result = await call(() => postForm("/api/biz/batch-ats", fd));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title">Batch ATS <span>Analyzer</span></h1>
      <p className="page-subtitle">Upload up to 10 resumes and screen them all against a job description at once.</p>

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone${dragOver ? " active" : ""}${files.length ? " active" : ""}`}
          onClick={() => document.getElementById("batch-resumes").click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        >
          <input id="batch-resumes" type="file" accept=".pdf,.txt,.docx,.doc" multiple onChange={(e) => handleFiles(e.target.files)} />
          <p className="drop-label">
            {files.length ? `${files.length} resume${files.length > 1 ? "s" : ""} selected` : "Drop resumes here or click to browse"}
          </p>
          <p className="drop-hint">PDF, DOCX, or TXT · up to 10 files</p>
        </div>
        {files.length > 0 && (
          <div style={{ marginBottom: "1rem" }}>
            {files.map((f, i) => (
              <p key={i} style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>📄 {f.name}</p>
            ))}
          </div>
        )}
        <textarea
          placeholder="Job description (paste here for better matching)"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={4}
          disabled={loading}
          style={{ width: "100%", padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical", marginBottom: "1rem" }}
        />
        <button type="submit" className="submit-btn" disabled={loading || !files.length}>
          {loading ? `Analyzing ${files.length} resume${files.length > 1 ? "s" : ""}…` : "Analyze All Resumes"}
        </button>
      </form>

      {error && <div className="error-banner" style={{ marginTop: "1rem" }}>{error}</div>}

      {data && (
        <div style={{ marginTop: "1.5rem" }}>
          <p className="page-subtitle">{data.total} resume{data.total !== 1 ? "s" : ""} analyzed</p>
          {(data.results || [])
            .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
            .map((result, i) => (
              <div key={i} className="result-card">
                {result.error ? (
                  <>
                    <p style={{ fontWeight: 700 }}>{result.filename}</p>
                    <p style={{ fontSize: "0.85rem", color: "#dc2626" }}>Error: {result.error}</p>
                  </>
                ) : (
                  <>
                    <div className="result-header">
                      <div>
                        <p style={{ fontWeight: 700, marginBottom: "0.2rem" }}>{result.candidate_name || result.filename}</p>
                        <p style={{ fontSize: "0.78rem", color: "var(--text-hint)" }}>{result.filename}</p>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        <span style={{ fontSize: "1.4rem", fontWeight: 800, color: LEVEL_COLOR[result.match_level] || "#666" }}>
                          {result.match_score}%
                        </span>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, color: REC_COLOR[result.recommendation] || "#666", background: "#f5f5f5", padding: "3px 10px", borderRadius: "20px" }}>
                          {result.recommendation}
                        </span>
                      </div>
                    </div>
                    {result.top_strengths?.length > 0 && (
                      <div style={{ marginTop: "0.6rem" }}>
                        <p style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-hint)", marginBottom: "0.3rem" }}>Strengths</p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                          {result.top_strengths.map((s, j) => <span key={j} style={{ background: "#dcfce7", color: "#16a34a", padding: "2px 8px", borderRadius: "12px", fontSize: "0.78rem" }}>{s}</span>)}
                        </div>
                      </div>
                    )}
                    {result.concerns?.length > 0 && (
                      <div style={{ marginTop: "0.5rem" }}>
                        <p style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-hint)", marginBottom: "0.3rem" }}>Concerns</p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                          {result.concerns.map((c, j) => <span key={j} style={{ background: "#fef2f2", color: "#dc2626", padding: "2px 8px", borderRadius: "12px", fontSize: "0.78rem" }}>{c}</span>)}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
