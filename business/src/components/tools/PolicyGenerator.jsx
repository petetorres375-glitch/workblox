import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, t) {
  const lines = [data.title || t("policyDocument"), "=".repeat(60), t("effective", { date: data.effective_date_placeholder || "" }), ""];
  if (data.purpose) lines.push(t("purpose"), "-".repeat(40), data.purpose, "");
  if (data.scope) lines.push(t("scope"), "-".repeat(40), data.scope, "");
  // Section headings come back from the model already in the report language.
  (data.sections || []).forEach((s) => { lines.push(s.heading, "-".repeat(40), s.content, ""); });
  if (data.acknowledgment_statement) lines.push(t("acknowledgment"), "-".repeat(40), data.acknowledgment_statement);
  return lines.join("\n");
}

function buildMd(data, t) {
  const lines = [`# ${data.title || t("policyDocument")}`, "", `*${t("effective", { date: data.effective_date_placeholder || "" })}*`];
  if (data.purpose) lines.push("", `## ${t("purpose")}`, data.purpose);
  if (data.scope) lines.push("", `## ${t("scope")}`, data.scope);
  (data.sections || []).forEach((s) => lines.push("", `## ${s.heading}`, s.content));
  if (data.acknowledgment_statement) lines.push("", `## ${t("acknowledgment")}`, `*${data.acknowledgment_statement}*`);
  return lines.join("\n");
}

export default function PolicyGenerator() {
  const { t, i18n } = useTranslation("policyGenerator");
  const { loading, error, call } = useApi();
  const [policyType, setPolicyType] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [specifics, setSpecifics] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/policy", { policy_type: policyType, company_name: companyName, industry, specifics, language: i18n.language }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder={t("policyTypePlaceholder")} value={policyType} onChange={(e) => setPolicyType(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("companyNamePlaceholder")} value={companyName} onChange={(e) => setCompanyName(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("industryPlaceholder")} value={industry} onChange={(e) => setIndustry(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder={t("specificsPlaceholder")} value={specifics} onChange={(e) => setSpecifics(e.target.value)} rows={3} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("generating") : t("generate")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{data.title}</strong></div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("policyDocument")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(buildTxt(data, t))}>{t("copyAll")}</button>
            </div>
            <p style={{ fontWeight: 800, fontSize: "1.1rem", marginBottom: "0.25rem" }}>{data.title}</p>
            <p style={{ fontSize: "0.82rem", color: "var(--text-hint)" }}>{t("effective", { date: data.effective_date_placeholder })}</p>
          </div>
          {data.purpose && (
            <div className="result-card">
              <p className="result-label">{t("purpose")}</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.purpose}</p>
            </div>
          )}
          {data.scope && (
            <div className="result-card">
              <p className="result-label">{t("scope")}</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{data.scope}</p>
            </div>
          )}
          {(data.sections || []).map((section, i) => (
            <div key={i} className="result-card">
              <p className="result-label">{section.heading}</p>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65, whiteSpace: "pre-wrap" }}>{section.content}</p>
            </div>
          ))}
          {data.acknowledgment_statement && (
            <div className="result-card">
              <p className="result-label">{t("acknowledgment")}</p>
              <p style={{ fontSize: "0.88rem", lineHeight: 1.6, fontStyle: "italic" }}>{data.acknowledgment_statement}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(policyType) || "policy"}
            subject={`${t("policyPrefix")} — ${data.title || policyType}`}
            txtContent={buildTxt(data, t)}
            mdContent={buildMd(data, t)}
          />
        </>
      )}
    </div>
  );
}
