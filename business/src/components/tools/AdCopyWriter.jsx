import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, platform, productService, t) {
  const lines = [`${t("docTitle")} — ${platform}${productService ? ` — ${productService}` : ""}`, "=".repeat(60)];
  if (data.headlines?.length) {
    lines.push("", t("headlines"), "-".repeat(40));
    data.headlines.forEach((h, i) => lines.push(`${i + 1}. ${h}`));
  }
  if (data.primary_descriptions?.length) {
    lines.push("", t("descriptions"), "-".repeat(40));
    data.primary_descriptions.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (data.cta_options?.length) lines.push("", t("ctaOptions"), "-".repeat(40), data.cta_options.join(" · "));
  if (data.value_propositions?.length) {
    lines.push("", t("valuePropositions"), "-".repeat(40));
    data.value_propositions.forEach((v, i) => lines.push(`${i + 1}. ${v}`));
  }
  return lines.join("\n");
}

function buildMd(data, platform, productService, t) {
  const title = productService ? `${t("docTitle")} — ${platform} — ${productService}` : `${t("docTitle")} — ${platform}`;
  const lines = [`# ${title}`];
  if (data.headlines?.length) { lines.push("", `## ${t("headlines")}`); data.headlines.forEach((h, i) => lines.push(`${i + 1}. ${h}`)); }
  if (data.primary_descriptions?.length) { lines.push("", `## ${t("descriptions")}`); data.primary_descriptions.forEach((d, i) => lines.push(`${i + 1}. ${d}`)); }
  if (data.cta_options?.length) { lines.push("", `## ${t("ctaOptions")}`); data.cta_options.forEach((c) => lines.push(`- ${c}`)); }
  if (data.value_propositions?.length) { lines.push("", `## ${t("valuePropositions")}`); data.value_propositions.forEach((v) => lines.push(`- ${v}`)); }
  return lines.join("\n");
}

export default function AdCopyWriter() {
  const { t, i18n } = useTranslation("adCopyWriter");
  const { loading, error, call } = useApi();
  const [productService, setProductService] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [platform, setPlatform] = useState("Google Ads");
  const [uniqueValue, setUniqueValue] = useState("");
  const [goal, setGoal] = useState("conversions");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/ad-copy", { product_service: productService, target_audience: targetAudience, platform, unique_value: uniqueValue, goal, language: i18n.language }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder={t("productServicePlaceholder")} value={productService} onChange={(e) => setProductService(e.target.value)} required rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <input type="text" placeholder={t("targetAudiencePlaceholder")} value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder={t("uniqueValuePlaceholder")} value={uniqueValue} onChange={(e) => setUniqueValue(e.target.value)} disabled={loading} style={inputStyle} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["Google Ads", "Facebook Ads", "Instagram Ads", "LinkedIn Ads", "TikTok Ads"].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select value={goal} onChange={(e) => setGoal(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["conversions", "awareness", "leads", "traffic", "app installs"].map(opt => <option key={opt} value={opt}>{t(`goalOptions.${opt}`)}</option>)}
          </select>
        </div>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("writing") : t("write")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{t("docTitle")} — {platform}{productService ? ` — ${productService}` : ""}</strong></div>
          {data.headlines?.length > 0 && (
            <div className="result-card">
              <div className="result-header">
                <p className="result-label">{t("headlines")}</p>
                <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.headlines.join("\n"))}>{t("copy")}</button>
              </div>
              {data.headlines.map((h, i) => <p key={i} style={{ fontSize: "0.92rem", fontWeight: 600, marginBottom: "0.4rem", lineHeight: 1.4 }}>{i + 1}. {h}</p>)}
            </div>
          )}
          {data.primary_descriptions?.length > 0 && (
            <div className="result-card">
              <div className="result-header">
                <p className="result-label">{t("descriptions")}</p>
                <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.primary_descriptions.join("\n\n"))}>{t("copy")}</button>
              </div>
              {data.primary_descriptions.map((d, i) => <p key={i} style={{ fontSize: "0.9rem", lineHeight: 1.6, marginBottom: "0.6rem" }}>{i + 1}. {d}</p>)}
            </div>
          )}
          {data.cta_options?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("ctaOptions")}</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {data.cta_options.map((cta, i) => (
                  <span key={i} style={{ background: "var(--orange)", color: "#fff", padding: "4px 12px", borderRadius: "20px", fontSize: "0.82rem", fontWeight: 700 }}>{cta}</span>
                ))}
              </div>
            </div>
          )}
          {data.value_propositions?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("valuePropositions")}</p>
              <ul className="section-list">{data.value_propositions.map((v, i) => <li key={i}>{v}</li>)}</ul>
            </div>
          )}
          <ReportToolbar
            filename={slug(productService) || "ad_copy"}
            subject={`${t("docTitle")} — ${platform}${productService ? ` — ${productService}` : ""}`}
            txtContent={buildTxt(data, platform, productService, t)}
            mdContent={buildMd(data, platform, productService, t)}
          />
        </>
      )}
    </div>
  );
}
