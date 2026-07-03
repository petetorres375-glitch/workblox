import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data) {
  const title = data.job_title || "Position";
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

function buildMd(data) {
  const title = data.job_title || "Position";
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
  const { t, i18n } = useTranslation("hiringManager");
  const { loading, error, call } = useApi();
  const [description, setDescription] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setData(null);
    const result = await call(() => post("/api/biz/hiring-manager", { description, language: i18n.language }));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea
          placeholder={t("descriptionPlaceholder")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={5}
          disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }}
        />
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? t("generating") : t("generate")}
        </button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}>
            <strong>Hiring Package — {data.job_title}</strong>
          </div>
          <div className="result-card">
            <p className="result-label">{t("positionSummary")}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.position_summary}</p>
          </div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("interviewQuestions")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText((data.interview_questions || []).join("\n"))}>{t("copy")}</button>
            </div>
            <ul className="section-list">{(data.interview_questions || []).map((q, i) => <li key={i}>{q}</li>)}</ul>
          </div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("evaluationCriteria")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText((data.evaluation_criteria || []).join("\n"))}>{t("copy")}</button>
            </div>
            <ul className="section-list">{(data.evaluation_criteria || []).map((c, i) => <li key={i}>{c}</li>)}</ul>
          </div>
          {data.red_flags?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("redFlags")}</p>
              <ul className="warning-list">{data.red_flags.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}
          {data.onboarding_tips?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("onboardingTips")}</p>
              <ul className="section-list">{data.onboarding_tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          <ReportToolbar
            filename={slug(data.job_title) || "hiring_package"}
            subject={`Hiring Package — ${data.job_title}`}
            txtContent={buildTxt(data)}
            mdContent={buildMd(data)}
          />
        </>
      )}
    </div>
  );
}
