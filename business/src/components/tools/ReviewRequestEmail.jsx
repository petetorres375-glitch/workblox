import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, t) {
  const lines = [t("docTitle"), "=".repeat(60)];
  if (data.subject) lines.push(`${t("subjectLine")}: ${data.subject}`);
  lines.push("", data.body || "");
  if (data.timing_advice) lines.push("", t("timingAdvice"), "-".repeat(40), data.timing_advice);
  return lines.join("\n");
}

function buildMd(data, t) {
  const lines = [`# ${t("docTitle")}`];
  if (data.subject) lines.push("", `**${t("subjectLine")}:** ${data.subject}`);
  lines.push("", `## ${t("emailBody")}`, data.body || "");
  if (data.timing_advice) lines.push("", `## ${t("timingAdvice")}`, data.timing_advice);
  return lines.join("\n");
}

export default function ReviewRequestEmail() {
  const { t, i18n } = useTranslation("reviewRequest");
  const { loading, error, call } = useApi();
  const [businessName, setBusinessName] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [serviceProvided, setServiceProvided] = useState("");
  const [platforms, setPlatforms] = useState("Google, Yelp");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/review-request", { business_name: businessName, customer_name: customerName, service_provided: serviceProvided, platforms, language: i18n.language }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder={t("businessNamePlaceholder")} value={businessName} onChange={(e) => setBusinessName(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("customerNamePlaceholder")} value={customerName} onChange={(e) => setCustomerName(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("serviceProvidedPlaceholder")} value={serviceProvided} onChange={(e) => setServiceProvided(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("platformsPlaceholder")} value={platforms} onChange={(e) => setPlatforms(e.target.value)} disabled={loading} style={inputStyle} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("writing") : t("write")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{t("docTitle")}{businessName ? ` — ${businessName}` : ""}</strong></div>
          {data.subject && (
            <div className="result-card">
              <p className="result-label">{t("subjectLine")}</p>
              <p style={{ fontWeight: 600 }}>{data.subject}</p>
            </div>
          )}
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("emailBody")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(`Subject: ${data.subject}\n\n${data.body}`)}>{t("copy")}</button>
            </div>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.body}</p>
          </div>
          {data.timing_advice && (
            <div className="result-card">
              <p className="result-label">{t("timingAdvice")}</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.timing_advice}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(businessName) || "review_request"}
            subject={`${t("docTitle")}${businessName ? ` — ${businessName}` : ""}`}
            txtContent={buildTxt(data, t)}
            mdContent={buildMd(data, t)}
          />
        </>
      )}
    </div>
  );
}
