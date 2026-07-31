import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar from "../ui/ReportToolbar";
import { reportTitle } from "../../utils/reportLabels";

function buildTxt(data, t) {
  const lines = [reportTitle(t), "=".repeat(60)];
  if (data.subject) lines.push(`${t("subjectLine")}: ${data.subject}`);
  lines.push("", data.response_draft || "");
  if (data.key_points_addressed?.length) {
    lines.push("", t("pointsAddressed"), "-".repeat(40));
    data.key_points_addressed.forEach((p, i) => lines.push(`${i + 1}. ${p}`));
  }
  if (data.follow_up_suggested) lines.push("", t("followUpSuggested"), "-".repeat(40), data.follow_up_suggested);
  return lines.join("\n");
}

function buildMd(data, t) {
  const lines = [`# ${reportTitle(t)}`];
  if (data.subject) lines.push("", `**${t("subjectLine")}:** ${data.subject}`);
  lines.push("", `## ${t("responseDraft")}`, data.response_draft || "");
  if (data.key_points_addressed?.length) { lines.push("", `## ${t("pointsAddressed")}`); data.key_points_addressed.forEach((p) => lines.push(`- ${p}`)); }
  if (data.follow_up_suggested) lines.push("", `## ${t("followUpSuggested")}`, data.follow_up_suggested);
  return lines.join("\n");
}

export default function CustomerResponseDrafter() {
  const { t, i18n } = useTranslation("customerResponse");
  const { loading, error, call } = useApi();
  const [customerMessage, setCustomerMessage] = useState("");
  const [context, setContext] = useState("");
  const [tone, setTone] = useState("professional");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/customer-response", { customer_message: customerMessage, context, tone, language: i18n.language }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder={t("customerMessagePlaceholder")} value={customerMessage} onChange={(e) => setCustomerMessage(e.target.value)} required rows={4} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <textarea placeholder={t("contextPlaceholder")} value={context} onChange={(e) => setContext(e.target.value)} rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <select value={tone} onChange={(e) => setTone(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
          {["professional", "empathetic", "apologetic", "firm", "friendly"].map(opt => (
            <option key={opt} value={opt}>{t(`tone.${opt}`)}</option>
          ))}
        </select>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("drafting") : t("draft")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Customer Response Draft</strong></div>
          {data.subject && (
            <div className="result-card">
              <p className="result-label">{t("subjectLine")}</p>
              <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>{data.subject}</p>
            </div>
          )}
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("responseDraft")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.response_draft)}>{t("copy")}</button>
            </div>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.response_draft}</p>
          </div>
          {data.key_points_addressed?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("pointsAddressed")}</p>
              <ul className="section-list">{data.key_points_addressed.map((p, i) => <li key={i}>{p}</li>)}</ul>
            </div>
          )}
          {data.follow_up_suggested && (
            <div className="result-card">
              <p className="result-label">{t("followUpSuggested")}</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.follow_up_suggested}</p>
            </div>
          )}
          <ReportToolbar
            filename="customer_response"
            subject="Customer Response Draft"
            txtContent={buildTxt(data, t)}
            mdContent={buildMd(data, t)}
          />
        </>
      )}
    </div>
  );
}
