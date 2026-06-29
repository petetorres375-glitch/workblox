import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, platform, productService) {
  const lines = [`AD COPY — ${platform.toUpperCase()}${productService ? ` — ${productService.toUpperCase()}` : ""}`, "=".repeat(60)];
  if (data.headlines?.length) {
    lines.push("", "HEADLINES", "-".repeat(40));
    data.headlines.forEach((h, i) => lines.push(`${i + 1}. ${h}`));
  }
  if (data.primary_descriptions?.length) {
    lines.push("", "DESCRIPTIONS", "-".repeat(40));
    data.primary_descriptions.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (data.cta_options?.length) lines.push("", "CALL-TO-ACTION OPTIONS", "-".repeat(40), data.cta_options.join(" · "));
  if (data.value_propositions?.length) {
    lines.push("", "VALUE PROPOSITIONS", "-".repeat(40));
    data.value_propositions.forEach((v, i) => lines.push(`${i + 1}. ${v}`));
  }
  return lines.join("\n");
}

function buildMd(data, platform, productService) {
  const title = productService ? `Ad Copy — ${platform} — ${productService}` : `Ad Copy — ${platform}`;
  const lines = [`# ${title}`];
  if (data.headlines?.length) { lines.push("", "## Headlines"); data.headlines.forEach((h, i) => lines.push(`${i + 1}. ${h}`)); }
  if (data.primary_descriptions?.length) { lines.push("", "## Descriptions"); data.primary_descriptions.forEach((d, i) => lines.push(`${i + 1}. ${d}`)); }
  if (data.cta_options?.length) { lines.push("", "## Call-to-Action Options"); data.cta_options.forEach((c) => lines.push(`- ${c}`)); }
  if (data.value_propositions?.length) { lines.push("", "## Value Propositions"); data.value_propositions.forEach((v) => lines.push(`- ${v}`)); }
  return lines.join("\n");
}

export default function AdCopyWriter() {
  const { loading, error, call } = useApi();
  const [productService, setProductService] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [platform, setPlatform] = useState("Google Ads");
  const [uniqueValue, setUniqueValue] = useState("");
  const [goal, setGoal] = useState("conversions");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/ad-copy", { product_service: productService, target_audience: targetAudience, platform, unique_value: uniqueValue, goal }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Ad Copy <span>Writer</span></h1>
      <p className="page-subtitle">Generate high-converting ad copy with multiple headline and description variations.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder="Product or service *" value={productService} onChange={(e) => setProductService(e.target.value)} required rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <input type="text" placeholder="Target audience (e.g. small business owners, age 25–45)" value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Unique value proposition" value={uniqueValue} onChange={(e) => setUniqueValue(e.target.value)} disabled={loading} style={inputStyle} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["Google Ads", "Facebook Ads", "Instagram Ads", "LinkedIn Ads", "TikTok Ads"].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select value={goal} onChange={(e) => setGoal(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["conversions", "awareness", "leads", "traffic", "app installs"].map(g => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
          </select>
        </div>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Writing…" : "Write Ad Copy"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Ad Copy — {platform}{productService ? ` — ${productService}` : ""}</strong></div>
          {data.headlines?.length > 0 && (
            <div className="result-card">
              <div className="result-header">
                <p className="result-label">Headlines</p>
                <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.headlines.join("\n"))}>Copy</button>
              </div>
              {data.headlines.map((h, i) => <p key={i} style={{ fontSize: "0.92rem", fontWeight: 600, marginBottom: "0.4rem", lineHeight: 1.4 }}>{i + 1}. {h}</p>)}
            </div>
          )}
          {data.primary_descriptions?.length > 0 && (
            <div className="result-card">
              <div className="result-header">
                <p className="result-label">Descriptions</p>
                <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.primary_descriptions.join("\n\n"))}>Copy</button>
              </div>
              {data.primary_descriptions.map((d, i) => <p key={i} style={{ fontSize: "0.9rem", lineHeight: 1.6, marginBottom: "0.6rem" }}>{i + 1}. {d}</p>)}
            </div>
          )}
          {data.cta_options?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Call-to-Action Options</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {data.cta_options.map((cta, i) => (
                  <span key={i} style={{ background: "var(--orange)", color: "#fff", padding: "4px 12px", borderRadius: "20px", fontSize: "0.82rem", fontWeight: 700 }}>{cta}</span>
                ))}
              </div>
            </div>
          )}
          {data.value_propositions?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Value Propositions</p>
              <ul className="section-list">{data.value_propositions.map((v, i) => <li key={i}>{v}</li>)}</ul>
            </div>
          )}
          <ReportToolbar
            filename={slug(productService) || "ad_copy"}
            subject={`Ad Copy — ${platform}${productService ? ` — ${productService}` : ""}`}
            txtContent={buildTxt(data, platform, productService)}
            mdContent={buildMd(data, platform, productService)}
          />
        </>
      )}
    </div>
  );
}
