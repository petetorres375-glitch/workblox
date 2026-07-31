import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { BASE_URL, postForm } from "../../api/client";
import { useApi } from "../../hooks/useApi";

const STEP_IDS = ["contact", "experience", "education", "skills", "review"];

const emptyJob = () => ({ title: "", company: "", dates: "", duties: "" });
const emptyEdu = () => ({ degree: "", school: "", year: "" });

export default function ResumeBuilder() {
  const { t, i18n } = useTranslation("resumeBuilder");
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
      language: i18n.language,
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
        // Section headings travel with the request — the PDF/DOCX/TXT are
        // rendered server-side, which has no translations of its own.
        body: JSON.stringify({
          ...result,
          labels: {
            summary:        t("result.summary"),
            experience:     t("result.workExperience"),
            education:      t("result.education"),
            skills:         t("result.skills"),
            certifications: t("result.certifications"),
          },
        }),
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
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      {/* Stepper */}
      {!result && (
        <div style={{ display: "flex", gap: 0, marginBottom: 24 }}>
          {STEP_IDS.map((id, i) => (
            <div key={id} style={{ flex: 1, textAlign: "center" }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%", margin: "0 auto 4px",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "0.8rem", fontWeight: 700,
                background: i === step ? "#2563eb" : i < step ? "#16a34a" : "#e5e7eb",
                color: i <= step ? "#fff" : "#6b7280",
              }}>{i < step ? "✓" : i + 1}</div>
              <div style={{ fontSize: "0.7rem", color: i === step ? "#2563eb" : "#9ca3af" }}>{t(`steps.${id}`)}</div>
            </div>
          ))}
        </div>
      )}

      {!result ? (
        <>
          {/* Step 0 — Contact */}
          {step === 0 && (
            <div className="result-card">
              <div className="result-label">{t("contact.sectionTitle")}</div>
              {[
                ["name", "name"],
                ["email", "email"],
                ["phone", "phone"],
                ["location", "location"],
                ["linkedin", "linkedin"],
              ].map(([field, key]) => (
                <div key={field} style={{ marginBottom: 10 }}>
                  <label style={labelStyle}>{t(`contact.${key}`)}</label>
                  <input
                    style={inputStyle}
                    value={contact[field]}
                    onChange={(e) => setContact((p) => ({ ...p, [field]: e.target.value }))}
                    placeholder={t(`contact.${key}`)}
                  />
                </div>
              ))}
              <div style={{ marginBottom: 10 }}>
                <label style={labelStyle}>{t("contact.jobRole")}</label>
                <input
                  style={inputStyle}
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  placeholder={t("contact.jobRolePlaceholder")}
                />
              </div>
            </div>
          )}

          {/* Step 1 — Experience */}
          {step === 1 && (
            <div className="result-card">
              <div className="result-label">{t("experience.sectionTitle")}</div>
              {experience.map((job, i) => (
                <div key={i} style={{ marginBottom: 20, paddingBottom: 16, borderBottom: i < experience.length - 1 ? "1px solid #e5e7eb" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{t("experience.job", { n: i + 1 })}</span>
                    {experience.length > 1 && (
                      <button onClick={() => removeJob(i)} style={removeBtnStyle}>{t("experience.remove")}</button>
                    )}
                  </div>
                  {[
                    ["title",   "title"],
                    ["company", "company"],
                    ["dates",   "dates"],
                  ].map(([field, key]) => (
                    <div key={field} style={{ marginBottom: 8 }}>
                      <label style={labelStyle}>{t(`experience.${key}`)}</label>
                      <input style={inputStyle} value={job[field]}
                        onChange={(e) => updateJob(i, field, e.target.value)}
                        placeholder={t(`experience.${key}`)} />
                    </div>
                  ))}
                  <div style={{ marginBottom: 8 }}>
                    <label style={labelStyle}>{t("experience.duties")}</label>
                    <textarea
                      style={{ ...inputStyle, height: 90, resize: "vertical" }}
                      value={job.duties}
                      onChange={(e) => updateJob(i, "duties", e.target.value)}
                      placeholder={t("experience.dutiesPlaceholder")}
                    />
                  </div>
                </div>
              ))}
              <button onClick={addJob} style={addBtnStyle}>{t("experience.addAnother")}</button>
            </div>
          )}

          {/* Step 2 — Education */}
          {step === 2 && (
            <div className="result-card">
              <div className="result-label">{t("education.sectionTitle")}</div>
              {education.map((e, i) => (
                <div key={i} style={{ marginBottom: 16, paddingBottom: 12, borderBottom: i < education.length - 1 ? "1px solid #e5e7eb" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{t("education.entry", { n: i + 1 })}</span>
                    {education.length > 1 && (
                      <button onClick={() => removeEdu(i)} style={removeBtnStyle}>{t("experience.remove")}</button>
                    )}
                  </div>
                  {[
                    ["degree", "degree"],
                    ["school", "school"],
                    ["year",   "year"],
                  ].map(([field, key]) => (
                    <div key={field} style={{ marginBottom: 8 }}>
                      <label style={labelStyle}>{t(`education.${key}`)}</label>
                      <input style={inputStyle} value={e[field]}
                        onChange={(ev) => updateEdu(i, field, ev.target.value)}
                        placeholder={t(`education.${key}`)} />
                    </div>
                  ))}
                </div>
              ))}
              <button onClick={addEdu} style={addBtnStyle}>{t("education.addAnother")}</button>
            </div>
          )}

          {/* Step 3 — Skills */}
          {step === 3 && (
            <div className="result-card">
              <div className="result-label">{t("skillsStep.sectionTitle")}</div>
              <div style={{ marginBottom: 12 }}>
                <label style={labelStyle}>{t("skillsStep.skills")}</label>
                <textarea style={{ ...inputStyle, height: 80, resize: "vertical" }}
                  value={skills} onChange={(e) => setSkills(e.target.value)}
                  placeholder={t("skillsStep.skillsPlaceholder")} />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label style={labelStyle}>{t("skillsStep.certifications")}</label>
                <input style={inputStyle} value={certifications}
                  onChange={(e) => setCerts(e.target.value)}
                  placeholder={t("skillsStep.certificationsPlaceholder")} />
              </div>
              <div style={{ marginBottom: 4 }}>
                <label style={labelStyle}>{t("skillsStep.extra")}</label>
                <textarea style={{ ...inputStyle, height: 60, resize: "vertical" }}
                  value={extra} onChange={(e) => setExtra(e.target.value)}
                  placeholder={t("skillsStep.extraPlaceholder")} />
              </div>
            </div>
          )}

          {error && <div className="error-banner" style={{ marginTop: 12 }}>{error}</div>}

          {/* Nav buttons */}
          <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
            {step > 0 && (
              <button className="copy-btn" onClick={() => setStep((s) => s - 1)}
                style={{ padding: "10px 22px" }}>
                {t("nav.back")}
              </button>
            )}
            {step < STEP_IDS.length - 1 ? (
              <button className="submit-btn" onClick={() => setStep((s) => s + 1)}
                disabled={!canNext()} style={{ flex: 1 }}>
                {t("nav.next")}
              </button>
            ) : (
              <button className="submit-btn" onClick={handleGenerate}
                disabled={loading} style={{ flex: 1 }}>
                {loading ? t("nav.generating") : t("nav.generate")}
              </button>
            )}
          </div>
        </>
      ) : (
        /* Result preview */
        <>
          <div className="result-card" style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div className="result-label" style={{ marginBottom: 0 }}>{t("result.ready")}</div>
              <button className="copy-btn" onClick={() => { setResult(null); setStep(0); }}
                style={{ fontSize: "0.8rem", padding: "4px 12px" }}>
                {t("result.startOver")}
              </button>
            </div>

            <div style={{ fontWeight: 700, fontSize: "1.4rem", color: "#0f172a" }}>{contact.name}</div>
            <div style={{ color: "#6b7280", fontSize: "0.85rem", marginBottom: 12 }}>
              {[contact.email, contact.phone, contact.location, contact.linkedin].filter(Boolean).join("  |  ")}
            </div>

            {result.resume?.summary && (
              <Section title={t("result.summary")}>
                <p style={{ color: "#374151", fontSize: "0.9rem", lineHeight: 1.6 }}>{result.resume.summary}</p>
              </Section>
            )}

            {result.resume?.experience?.map((job, i) => (
              <Section key={i} title={i === 0 ? t("result.workExperience") : null}>
                <div style={{ fontWeight: 600, color: "#0f172a" }}>{job.title} — <span style={{ fontWeight: 400, color: "#6b7280" }}>{job.company} | {job.dates}</span></div>
                <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
                  {job.bullets?.map((b, j) => (
                    <li key={j} style={{ color: "#374151", fontSize: "0.9rem", marginBottom: 3 }}>{b}</li>
                  ))}
                </ul>
              </Section>
            ))}

            {result.resume?.education?.length > 0 && (
              <Section title={t("result.education")}>
                {result.resume.education.map((e, i) => (
                  <div key={i} style={{ marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{e.degree}</span>
                    <span style={{ color: "#6b7280" }}> — {e.school} {e.year && `| ${e.year}`}</span>
                  </div>
                ))}
              </Section>
            )}

            {result.resume?.skills?.length > 0 && (
              <Section title={t("result.skills")}>
                <div style={{ color: "#374151", fontSize: "0.9rem" }}>
                  {result.resume.skills.join(" • ")}
                </div>
              </Section>
            )}

            {result.resume?.certifications?.filter(Boolean).length > 0 && (
              <Section title={t("result.certifications")}>
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
              {downloading === "txt" ? t("download.saving") : t("download.txt")}
            </button>
            <button className="copy-btn" onClick={() => download("pdf")}
              disabled={downloading === "pdf"}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              {downloading === "pdf" ? t("download.generating") : t("download.pdf")}
            </button>
            <button className="copy-btn" onClick={() => download("docx")}
              disabled={downloading === "docx"}
              style={{ padding: "8px 18px", fontSize: "0.88rem" }}>
              {downloading === "docx" ? t("download.generating") : t("download.word")}
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
