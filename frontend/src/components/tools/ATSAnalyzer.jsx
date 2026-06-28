import { useEffect, useRef, useState } from "react";
import { BASE_URL, postForm } from "../../api/client";
import { useApi } from "../../hooks/useApi";

const PRIORITY_COLORS = { high: "#dc2626", medium: "#d97706", low: "#2563eb" };

export default function ATSAnalyzer() {
  const [file, setFile]           = useState(null);
  const [dragOver, setDragOver]   = useState(false);
  const [clientName, setClientName] = useState("");
  const [jobRole, setJobRole]     = useState("");
  const [roles, setRoles]         = useState([]);
  const [data, setData]           = useState(null);
  const [downloading, setDownloading] = useState(null);
  const fileRef = useRef();
  const { loading, error, call }  = useApi();

  useEffect(() => {
    const token = localStorage.getItem("wb_token");
    fetch(`${BASE_URL}/api/ats/roles`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setRoles(data); })
      .catch(() => {});
  }, []);

  function handleFile(f) {
    if (f) { setFile(f); setData(null); }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("resume", file);
    if (clientName.trim()) fd.append("client_name", clientName.trim());
    if (jobRole)           fd.append("job_role", jobRole);
    const result = await call(() => postForm("/api/ats", fd));
    if (result) setData(result);
  }

  async function download(fmt) {
    if (!data) return;
    setDownloading(fmt);
    try {
      const res = await fetch(`${BASE_URL}/api/ats/download/${fmt}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          results:     data.results,
          client_name: data.client_name,
          filename:    data.filename,
          job_role:    data.job_role,
          now:         data.now,
        }),
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `ATS_Report_${(data.client_name || "Client").replace(/\s+/g, "_")}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message);
    } finally {
      setDownloading(null);
    }
  }

  function downloadTxt() {
    if (!data) return;
    const lines = [
      `ATS RESUME ANALYZER — REPORT`,
      `Client : ${data.client_name}`,
      `File   : ${data.filename}`,
      `Date   : ${data.now}`,
      `Score  : ${data.results.score} / 100  (${data.grade})`,
      "",
    ];
    const r = data.results;
    if (r.recommendations?.length) {
      lines.push("RECOMMENDATIONS", "-".repeat(40));
      r.recommendations.forEach((rec, i) => {
        lines.push(`${i + 1}. [${rec.priority.toUpperCase()}] ${rec.title}`);
        lines.push(`   ${rec.detail}`);
        lines.push("");
      });
    }
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url;
    a.download = `ATS_Report_${(data.client_name || "Client").replace(/\s+/g, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const score       = data?.results?.score ?? null;
  const scoreColor  = score >= 65 ? "#16a34a" : score >= 50 ? "#d97706" : "#dc2626";

  return (
    <>
      <h1 className="page-title">ATS <span>Analyzer</span></h1>
      <p className="page-subtitle">Upload a resume — get an instant ATS score, keyword gaps, and recommendations.</p>

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone${dragOver ? " active" : ""}`}
          onClick={() => fileRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <p className="drop-label" style={{ color: "#111" }}>{file.name}</p>
          ) : (
            <>
              <p className="drop-label">Drop a resume here or click to browse</p>
              <p className="drop-hint">TXT, PDF, or DOCX — max 5 MB</p>
            </>
          )}
        </div>

        <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Client name (optional)"
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            style={{
              flex: 1, minWidth: 180, padding: "0.7rem 1rem",
              background: "#fff", border: "1.5px solid #ddd",
              borderRadius: 8, fontFamily: "inherit", fontSize: "0.95rem",
            }}
          />
          <select
            value={jobRole}
            onChange={(e) => setJobRole(e.target.value)}
            style={{
              flex: 1, minWidth: 180, padding: "0.7rem 1rem",
              background: "#fff", border: "1.5px solid #ddd",
              borderRadius: 8, fontFamily: "inherit", fontSize: "0.95rem",
            }}
          >
            <option value="">Job role (optional)</option>
            {roles.map((r) => (
              <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
            ))}
          </select>
        </div>

        <button type="submit" className="submit-btn" disabled={loading || !file}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
      </form>

      {error && <div className="error-banner" style={{ marginTop: 16 }}>{error}</div>}

      {data && !loading && (
        <>
          {/* Score card */}
          <div className="result-card" style={{ marginTop: 24, textAlign: "center" }}>
            <div style={{ fontSize: "4rem", fontWeight: 700, color: scoreColor, lineHeight: 1 }}>
              {score}
            </div>
            <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>out of 100</div>
            <div style={{ fontWeight: 600, fontSize: "1.1rem", marginTop: 4 }}>{data.grade}</div>
            <div style={{ color: "#6b7280", fontSize: "0.85rem", marginTop: 4 }}>
              {data.results.total_found} / {data.results.total_possible} keywords found
            </div>
            <ScoreBar score={score} color={scoreColor} />
          </div>

          {/* Contact check */}
          <ContactCheck contact={data.results.contact} />

          {/* Recommendations */}
          {data.results.recommendations?.length > 0 && (
            <div className="result-card" style={{ marginTop: 16 }}>
              <div className="result-label">Recommendations</div>
              {data.results.recommendations.map((rec, i) => (
                <div key={i} style={{ marginBottom: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{
                      fontSize: "0.65rem", fontWeight: 700, letterSpacing: "0.08em",
                      color: PRIORITY_COLORS[rec.priority], textTransform: "uppercase",
                      border: `1px solid ${PRIORITY_COLORS[rec.priority]}`,
                      borderRadius: 4, padding: "1px 6px",
                    }}>
                      {rec.priority}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{rec.title}</span>
                  </div>
                  <p style={{ color: "#6b7280", fontSize: "0.88rem", marginTop: 4, marginBottom: 0 }}>
                    {rec.detail}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Keyword breakdown */}
          <div className="result-card" style={{ marginTop: 16 }}>
            <div className="result-label">Keyword Breakdown</div>
            {Object.entries(data.results.categories).map(([cat, d]) => {
              const pct = d.total ? Math.round((d.score / d.total) * 100) : 0;
              return (
                <div key={cat} style={{ marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{cat}</span>
                    <span style={{ color: "#6b7280", fontSize: "0.85rem" }}>{d.score}/{d.total} ({pct}%)</span>
                  </div>
                  <ScoreBar score={pct} color={pct >= 65 ? "#16a34a" : pct >= 40 ? "#d97706" : "#dc2626"} />
                  {d.found.length > 0 && (
                    <div style={{ marginTop: 4 }}>
                      {d.found.map((kw) => <Chip key={kw} label={kw} found />)}
                    </div>
                  )}
                  {d.missing.length > 0 && (
                    <div style={{ marginTop: 4 }}>
                      {d.missing.slice(0, 8).map((kw) => <Chip key={kw} label={kw} found={false} />)}
                      {d.missing.length > 8 && (
                        <span style={{ fontSize: "0.78rem", color: "#9ca3af" }}>+{d.missing.length - 8} more</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Job match */}
          {data.results.job_match && (
            <div className="result-card" style={{ marginTop: 16 }}>
              <div className="result-label">Job Match: {data.results.job_match.role}</div>
              <div style={{ fontWeight: 600, color: "#2563eb", marginBottom: 8 }}>
                {data.results.job_match.score} / {data.results.job_match.total} keywords matched
              </div>
              {data.results.job_match.found.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  {data.results.job_match.found.map((kw) => <Chip key={kw} label={kw} found />)}
                </div>
              )}
              {data.results.job_match.missing.length > 0 && (
                <div>
                  {data.results.job_match.missing.map((kw) => <Chip key={kw} label={kw} found={false} />)}
                </div>
              )}
            </div>
          )}

          {/* Downloads */}
          <div style={{ marginTop: 16, display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
            <button className="copy-btn" onClick={downloadTxt}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              ↓ TXT
            </button>
            <button className="copy-btn" onClick={() => download("pdf")}
              disabled={downloading === "pdf"}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              {downloading === "pdf" ? "Generating..." : "↓ PDF"}
            </button>
            <button className="copy-btn" onClick={() => download("docx")}
              disabled={downloading === "docx"}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              {downloading === "docx" ? "Generating..." : "↓ Word"}
            </button>
          </div>
        </>
      )}
    </>
  );
}

function ScoreBar({ score, color }) {
  return (
    <div style={{ background: "#e5e7eb", borderRadius: 4, height: 6, marginTop: 8, overflow: "hidden" }}>
      <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.6s ease" }} />
    </div>
  );
}

function Chip({ label, found }) {
  return (
    <span style={{
      display: "inline-block", margin: "2px 3px",
      padding: "2px 8px", borderRadius: 4, fontSize: "0.78rem",
      background: found ? "#dcfce7" : "#fee2e2",
      color: found ? "#16a34a" : "#dc2626",
    }}>
      {found ? "+ " : "- "}{label}
    </span>
  );
}

function ContactCheck({ contact }) {
  const fields = [
    { key: "email", label: "Email" },
    { key: "phone", label: "Phone" },
    { key: "linkedin", label: "LinkedIn" },
    { key: "location", label: "Location" },
  ];
  return (
    <div className="result-card" style={{ marginTop: 16, display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
      {fields.map(({ key, label }) => (
        <span key={key} style={{
          padding: "4px 12px", borderRadius: 6, fontSize: "0.82rem", fontWeight: 600,
          background: contact[key] ? "#dcfce7" : "#fee2e2",
          color: contact[key] ? "#16a34a" : "#dc2626",
        }}>
          {contact[key] ? "✓" : "✗"} {label}
        </span>
      ))}
    </div>
  );
}
