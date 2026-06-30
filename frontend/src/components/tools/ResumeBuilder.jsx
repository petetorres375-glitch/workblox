import { useState } from "react";
import { BASE_URL, postForm } from "../../api/client";
import { useApi } from "../../hooks/useApi";

const STEPS = ["Contact", "Experience", "Education", "Skills", "Review"];

const emptyJob = () => ({ title: "", company: "", dates: "", duties: "" });
const emptyEdu = () => ({ degree: "", school: "", year: "" });

export default function ResumeBuilder() {
  const [step, setStep]           = useState(0);
  const [contact, setContact]     = useState({ name: "", email: "", phone: "", location: "", linkedin: "" });
  const [jobRole, setJobRole]     = useState("");
  const [experience, setExp]      = useState([emptyJob()]);
  const [education, setEdu]       = useState([emptyEdu()]);
  const [skills, setSkills]       = useState("");
  const [certifications, setCerts] = useState("");
  const [extra, setExtra]         = useState("");
  const [result, setResult]       = useState(null);
  const [downloading, setDl]      = useState(null);
  const { loading, error, call }  = useApi();

  // --- experience helpers ---
  function updateJob(i, field, val) {
    setExp((prev) => prev.map((j, idx) => idx === i ? { ...j, [field]: val } : j));
  }
  function addJob()    { setExp((p) => [...p, emptyJob()]); }
  function removeJob(i) { setExp((p) => p.filter((_, idx) => idx !== i)); }

  // --- education helpers ---
  function updateEdu(i, field, val) {
    setEdu((prev) => prev.map((e, idx) => idx === i ? { ...e, [field]: val } : e));
  }
  function addEdu()    { setEdu((p) => [...p, emptyEdu()]); }
  function removeEdu(i) { setEdu((p) => p.filter((_, idx) => idx !== i)); }

  async function handleGenerate() {
    const payload = {
      name: contact.name, email: contact.email, phone: contact.phone,
      location: contact.location, linkedin: contact.linkedin,
      job_role: jobRole, experience, education,
      skills, certifications, extra,
    };
    const res = await call(() =>
      fetch(`${BASE_URL}/api/resume/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("wb_token")}` },
        body: JSON.stringify(payload),
      }).then((r) => r.ok ? r.json() : r.json().then((d) => Promise.reject(new Error(d.error || "Failed"))))
    );
    if (res) setResult(res);
  }

  async function download(fmt) {
    if (!result) return;
    setDl(fmt);
    try {
      const res = await fetch(`${BASE_URL}/api/resume/download/${fmt}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("wb_token")}` },
        body: JSON.stringify(result),
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `${(contact.name || "Resume").replace(/\s+/g, "_")}_Resume.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message);
    } finally {
      setDl(null);
    }
  }

  function canNext() {
    if (step === 0) return contact.name.trim().length > 0;
    if (step === 1) return experience.some((j) => j.title.trim() || j.duties.trim());
    return true;
  }

  return (
    <>
      <h1 className="page-title">Resume <span>Builder</span></h1>
      <p className="page-subtitle">Fill in your info — Claude writes a polished, ATS-optimized resume.</p>

      {/* Stepper */}
      {!result && (
        <div style={{ display: "flex", gap: 0, marginBottom: 24 }}>
          {STEPS.map((label, i) => (
            <div key={i} style={{ flex: 1, textAlign: "center" }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%", margin: "0 auto 4px",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "0.8rem", fontWeight: 700,
                background: i === step ? "#2563eb" : i < step ? "#16a34a" : "#e5e7eb",
                color: i <= step ? "#fff" : "#6b7280",
              }}>{i < step ? "✓" : i + 1}</div>
              <div style={{ fontSize: "0.7rem", color: i === step ? "#2563eb" : "#9ca3af" }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {!result ? (
        <>
          {/* Step 0 — Contact */}
          {step === 0 && (
            <div className="result-card">
              <div className="result-label">Contact Information</div>
              {[
                ["name", "Full Name *"],
                ["email", "Email"],
                ["phone", "Phone"],
                ["location", "City, State"],
                ["linkedin", "LinkedIn URL"],
              ].map(([field, label]) => (
                <div key={field} style={{ marginBottom: 10 }}>
                  <label style={labelStyle}>{label}</label>
                  <input
                    style={inputStyle}
                    value={contact[field]}
                    onChange={(e) => setContact((p) => ({ ...p, [field]: e.target.value }))}
                    placeholder={label}
                  />
                </div>
              ))}
              <div style={{ marginBottom: 10 }}>
                <label style={labelStyle}>Target Job Role</label>
                <input
                  style={inputStyle}
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  placeholder="e.g. Customer Service, Event Server, Bookkeeper"
                />
              </div>
            </div>
          )}

          {/* Step 1 — Experience */}
          {step === 1 && (
            <div className="result-card">
              <div className="result-label">Work Experience</div>
              {experience.map((job, i) => (
                <div key={i} style={{ marginBottom: 20, paddingBottom: 16, borderBottom: i < experience.length - 1 ? "1px solid #e5e7eb" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Job {i + 1}</span>
                    {experience.length > 1 && (
                      <button onClick={() => removeJob(i)} style={removeBtnStyle}>Remove</button>
                    )}
                  </div>
                  {[
                    ["title",   "Job Title"],
                    ["company", "Company Name"],
                    ["dates",   "Dates (e.g. 2020 – 2023)"],
                  ].map(([field, label]) => (
                    <div key={field} style={{ marginBottom: 8 }}>
                      <label style={labelStyle}>{label}</label>
                      <input style={inputStyle} value={job[field]}
                        onChange={(e) => updateJob(i, field, e.target.value)}
                        placeholder={label} />
                    </div>
                  ))}
                  <div style={{ marginBottom: 8 }}>
                    <label style={labelStyle}>Duties & Achievements — describe what you did, Claude will polish it</label>
                    <textarea
                      style={{ ...inputStyle, height: 90, resize: "vertical" }}
                      value={job.duties}
                      onChange={(e) => updateJob(i, "duties", e.target.value)}
                      placeholder="e.g. Handled customer calls, managed scheduling, trained new staff, resolved complaints..."
                    />
                  </div>
                </div>
              ))}
              <button onClick={addJob} style={addBtnStyle}>+ Add Another Job</button>
            </div>
          )}

          {/* Step 2 — Education */}
          {step === 2 && (
            <div className="result-card">
              <div className="result-label">Education</div>
              {education.map((e, i) => (
                <div key={i} style={{ marginBottom: 16, paddingBottom: 12, borderBottom: i < education.length - 1 ? "1px solid #e5e7eb" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Entry {i + 1}</span>
                    {education.length > 1 && (
                      <button onClick={() => removeEdu(i)} style={removeBtnStyle}>Remove</button>
                    )}
                  </div>
                  {[
                    ["degree", "Degree / Diploma / Certificate"],
                    ["school", "School / Institution"],
                    ["year",   "Year Completed"],
                  ].map(([field, label]) => (
                    <div key={field} style={{ marginBottom: 8 }}>
                      <label style={labelStyle}>{label}</label>
                      <input style={inputStyle} value={e[field]}
                        onChange={(ev) => updateEdu(i, field, ev.target.value)}
                        placeholder={label} />
                    </div>
                  ))}
                </div>
              ))}
              <button onClick={addEdu} style={addBtnStyle}>+ Add Another</button>
            </div>
          )}

          {/* Step 3 — Skills */}
          {step === 3 && (
            <div className="result-card">
              <div className="result-label">Skills & More</div>
              <div style={{ marginBottom: 12 }}>
                <label style={labelStyle}>Skills — list anything you know</label>
                <textarea style={{ ...inputStyle, height: 80, resize: "vertical" }}
                  value={skills} onChange={(e) => setSkills(e.target.value)}
                  placeholder="e.g. Microsoft Office, Excel, customer service, bilingual, forklift, QuickBooks..." />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label style={labelStyle}>Certifications (optional)</label>
                <input style={inputStyle} value={certifications}
                  onChange={(e) => setCerts(e.target.value)}
                  placeholder="e.g. ServSafe, CompTIA A+, CPR Certified" />
              </div>
              <div style={{ marginBottom: 4 }}>
                <label style={labelStyle}>Anything else to include? (optional)</label>
                <textarea style={{ ...inputStyle, height: 60, resize: "vertical" }}
                  value={extra} onChange={(e) => setExtra(e.target.value)}
                  placeholder="Languages spoken, volunteer work, awards, special notes..." />
              </div>
            </div>
          )}

          {error && <div className="error-banner" style={{ marginTop: 12 }}>{error}</div>}

          {/* Nav buttons */}
          <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
            {step > 0 && (
              <button className="copy-btn" onClick={() => setStep((s) => s - 1)}
                style={{ padding: "10px 22px" }}>
                ← Back
              </button>
            )}
            {step < STEPS.length - 1 ? (
              <button className="submit-btn" onClick={() => setStep((s) => s + 1)}
                disabled={!canNext()} style={{ flex: 1 }}>
                Next →
              </button>
            ) : (
              <button className="submit-btn" onClick={handleGenerate}
                disabled={loading} style={{ flex: 1 }}>
                {loading ? "Claude is writing your resume..." : "Generate Resume"}
              </button>
            )}
          </div>
        </>
      ) : (
        /* Result preview */
        <>
          <div className="result-card" style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div className="result-label" style={{ marginBottom: 0 }}>Resume Ready</div>
              <button className="copy-btn" onClick={() => { setResult(null); setStep(0); }}
                style={{ fontSize: "0.8rem", padding: "4px 12px" }}>
                Start Over
              </button>
            </div>

            <div style={{ fontWeight: 700, fontSize: "1.4rem", color: "#0f172a" }}>{contact.name}</div>
            <div style={{ color: "#6b7280", fontSize: "0.85rem", marginBottom: 12 }}>
              {[contact.email, contact.phone, contact.location, contact.linkedin].filter(Boolean).join("  |  ")}
            </div>

            {result.resume?.summary && (
              <Section title="Professional Summary">
                <p style={{ color: "#374151", fontSize: "0.9rem", lineHeight: 1.6 }}>{result.resume.summary}</p>
              </Section>
            )}

            {result.resume?.experience?.map((job, i) => (
              <Section key={i} title={i === 0 ? "Work Experience" : null}>
                <div style={{ fontWeight: 600, color: "#0f172a" }}>{job.title} — <span style={{ fontWeight: 400, color: "#6b7280" }}>{job.company} | {job.dates}</span></div>
                <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
                  {job.bullets?.map((b, j) => (
                    <li key={j} style={{ color: "#374151", fontSize: "0.9rem", marginBottom: 3 }}>{b}</li>
                  ))}
                </ul>
              </Section>
            ))}

            {result.resume?.education?.length > 0 && (
              <Section title="Education">
                {result.resume.education.map((e, i) => (
                  <div key={i} style={{ marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{e.degree}</span>
                    <span style={{ color: "#6b7280" }}> — {e.school} {e.year && `| ${e.year}`}</span>
                  </div>
                ))}
              </Section>
            )}

            {result.resume?.skills?.length > 0 && (
              <Section title="Skills">
                <div style={{ color: "#374151", fontSize: "0.9rem" }}>
                  {result.resume.skills.join(" • ")}
                </div>
              </Section>
            )}

            {result.resume?.certifications?.filter(Boolean).length > 0 && (
              <Section title="Certifications">
                {result.resume.certifications.filter(Boolean).map((c, i) => (
                  <div key={i} style={{ color: "#374151", fontSize: "0.9rem" }}>• {c}</div>
                ))}
              </Section>
            )}
          </div>

          <div style={{ marginTop: 16, display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
            <button className="copy-btn" onClick={() => download("txt")}
              disabled={downloading === "txt"}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              {downloading === "txt" ? "Saving..." : "↓ TXT"}
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

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {title && (
        <>
          <div style={{ fontWeight: 700, fontSize: "0.75rem", letterSpacing: "0.08em",
            color: "#2563eb", textTransform: "uppercase", marginBottom: 4 }}>{title}</div>
          <hr style={{ border: "none", borderTop: "1.5px solid #e5e7eb", marginBottom: 8 }} />
        </>
      )}
      {children}
    </div>
  );
}

const labelStyle = {
  display: "block", fontSize: "0.78rem", fontWeight: 600,
  color: "#6b7280", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em",
};

const inputStyle = {
  width: "100%", padding: "0.65rem 0.9rem", boxSizing: "border-box",
  background: "#f9fafb", border: "1.5px solid #e5e7eb",
  borderRadius: 8, fontFamily: "inherit", fontSize: "0.95rem", color: "#111",
};

const addBtnStyle = {
  background: "none", border: "1.5px dashed #d1d5db", borderRadius: 8,
  padding: "8px 16px", color: "#6b7280", cursor: "pointer",
  fontSize: "0.88rem", fontFamily: "inherit", marginTop: 4,
};

const removeBtnStyle = {
  background: "none", border: "none", color: "#dc2626",
  cursor: "pointer", fontSize: "0.8rem", fontFamily: "inherit",
};
