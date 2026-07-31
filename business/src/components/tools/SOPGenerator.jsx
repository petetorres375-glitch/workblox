import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";
import { reportTitle } from "../../utils/reportLabels";

function buildTxt(data, t) {
  const lines = [data.title || reportTitle(t), "=".repeat(60), t("frequencyLabel", { frequency: data.frequency || "" }), "", t("overview"), "-".repeat(40), data.purpose || ""];
  if (data.required_tools?.length) {
    lines.push("", t("requiredTools"), "-".repeat(40));
    data.required_tools.forEach((t, i) => lines.push(`${i + 1}. ${t}`));
  }
  if (data.steps?.length) {
    lines.push("", t("steps"), "-".repeat(40));
    data.steps.forEach((step) => {
      lines.push(``, t("stepLabel", { number: step.step_number, action: step.action }), step.details || "");
      if (step.warning) lines.push(`⚠ ${step.warning}`);
    });
  }
  if (data.quality_checks?.length) {
    lines.push("", t("qualityChecks"), "-".repeat(40));
    data.quality_checks.forEach((q, i) => lines.push(`${i + 1}. ${q}`));
  }
  if (data.notes) lines.push("", t("notes"), "-".repeat(40), data.notes);
  return lines.join("\n");
}

function buildMd(data, t) {
  const lines = [`# ${data.title || reportTitle(t)}`, "", `**${t("frequencyLabel", { frequency: data.frequency || "" })}**`, "", `## ${t("overview")}`, data.purpose || ""];
  if (data.required_tools?.length) { lines.push("", `## ${t("requiredTools")}`); data.required_tools.forEach((t) => lines.push(`- ${t}`)); }
  if (data.steps?.length) {
    lines.push("", `## ${t("steps")}`);
    data.steps.forEach((step) => {
      lines.push("", `### ${t("stepLabel", { number: step.step_number, action: step.action })}`, step.details || "");
      if (step.warning) lines.push("", `> ⚠ ${step.warning}`);
    });
  }
  if (data.quality_checks?.length) { lines.push("", `## ${t("qualityChecks")}`); data.quality_checks.forEach((q) => lines.push(`- ${q}`)); }
  if (data.notes) lines.push("", `## ${t("notes")}`, data.notes);
  return lines.join("\n");
}

export default function SOPGenerator() {
  const { t, i18n } = useTranslation("sopGenerator");
  const { loading, error, call } = useApi();
  const [processName, setProcessName] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [frequency, setFrequency] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/sop", { process_name: processName, department, description, frequency, language: i18n.language }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder={t("processNamePlaceholder")} value={processName} onChange={(e) => setProcessName(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("departmentPlaceholder")} value={department} onChange={(e) => setDepartment(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("frequencyPlaceholder")} value={frequency} onChange={(e) => setFrequency(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder={t("descriptionPlaceholder")} value={description} onChange={(e) => setDescription(e.target.value)} required rows={3} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("generating") : t("generate")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{data.title}</strong></div>
          <div className="result-card">
            <p className="result-label">{t("overview")}</p>
            <p style={{ fontWeight: 800, fontSize: "1.05rem", marginBottom: "0.4rem" }}>{data.title}</p>
            <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>{t("frequencyLabel", { frequency: data.frequency })}</p>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.purpose}</p>
          </div>
          {data.required_tools?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("requiredTools")}</p>
              <ul className="section-list">{data.required_tools.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          {data.steps?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("steps")}</p>
              {data.steps.map((step, i) => (
                <div key={i} style={{ marginBottom: "1rem", paddingLeft: "1rem", borderLeft: "3px solid var(--orange)" }}>
                  <p style={{ fontWeight: 700, marginBottom: "0.2rem" }}>{t("stepLabel", { number: step.step_number, action: step.action })}</p>
                  <p style={{ fontSize: "0.9rem", lineHeight: 1.6, color: "var(--text-muted)" }}>{step.details}</p>
                  {step.warning && <p style={{ fontSize: "0.82rem", color: "#b45309", marginTop: "0.25rem" }}>⚠ {step.warning}</p>}
                </div>
              ))}
            </div>
          )}
          {data.quality_checks?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("qualityChecks")}</p>
              <ul className="section-list">{data.quality_checks.map((q, i) => <li key={i}>{q}</li>)}</ul>
            </div>
          )}
          {data.notes && (
            <div className="result-card">
              <p className="result-label">{t("notes")}</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.notes}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(processName) || "sop"}
            subject={`${reportTitle(t)} — ${data.title || processName}`}
            txtContent={buildTxt(data, t)}
            mdContent={buildMd(data, t)}
          />
        </>
      )}
    </div>
  );
}
